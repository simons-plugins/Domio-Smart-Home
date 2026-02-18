#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Log API - Exposes Indigo event log as JSON API
#
# Endpoints:
#   GET /message/com.simons-plugins.indigo-log-api/log?lines=500&source=X&search=Y
#   GET /message/com.simons-plugins.indigo-log-api/sources
#
try:
    import indigo
except ImportError:
    pass

import json


class Plugin(indigo.PluginBase):

    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs, **kwargs):
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs, **kwargs)
        self.debug = False

    def startup(self):
        self.logger.info("Log API started")

    def shutdown(self):
        self.logger.info("Log API stopped")

    # MARK: - HTTP Handlers

    def log(self, action, dev=None, caller_waiting_for_result=None):
        """Return event log entries as JSON.

        Query params:
            lines  - number of entries (default from plugin config)
            source - filter by TypeStr (plugin source name)
            search - text search in Message field
        """
        reply = indigo.Dict()
        reply["headers"] = indigo.Dict({"Content-Type": "application/json"})

        try:
            props = dict(action.props)
            query_args = props.get("url_query_args", {})

            # Parse line count
            default_lines = int(self.pluginPrefs.get("defaultLineCount", 500))
            try:
                line_count = int(query_args.get("lines", default_lines))
            except (ValueError, TypeError):
                line_count = default_lines
            line_count = max(1, min(line_count, 5000))

            # Get log entries
            raw_entries = indigo.server.getEventLogList(
                returnAsList=True,
                showTimeStamp=True,
                lineCount=line_count,
            )

            # Build response entries with optional filtering
            source_filter = query_args.get("source", "").strip()
            search_filter = query_args.get("search", "").strip().lower()

            entries = []
            for entry in raw_entries:
                entry_dict = dict(entry)
                message = entry_dict.get("Message", "")
                source = entry_dict.get("TypeStr", "")
                type_val = entry_dict.get("TypeVal", 0)
                timestamp = entry_dict.get("TimeStamp", "")

                # Apply source filter
                if source_filter and source != source_filter:
                    continue

                # Apply search filter
                if search_filter and search_filter not in message.lower():
                    continue

                entries.append({
                    "message": message,
                    "source": source,
                    "typeVal": type_val,
                    "timestamp": str(timestamp),
                })

            result = {
                "success": True,
                "count": len(entries),
                "entries": entries,
            }

            reply["status"] = 200
            reply["content"] = json.dumps(result, indent=None)

        except Exception as exc:
            self.logger.exception(exc)
            reply["status"] = 500
            reply["content"] = json.dumps({"success": False, "error": str(exc)})

        return reply

    def sources(self, action, dev=None, caller_waiting_for_result=None):
        """Return distinct log source names (TypeStr values) from recent log."""
        reply = indigo.Dict()
        reply["headers"] = indigo.Dict({"Content-Type": "application/json"})

        try:
            raw_entries = indigo.server.getEventLogList(
                returnAsList=True,
                showTimeStamp=True,
                lineCount=2000,
            )

            source_set = set()
            for entry in raw_entries:
                entry_dict = dict(entry)
                source = entry_dict.get("TypeStr", "")
                if source:
                    source_set.add(source)

            result = {"sources": sorted(source_set)}

            reply["status"] = 200
            reply["content"] = json.dumps(result, indent=None)

        except Exception as exc:
            self.logger.exception(exc)
            reply["status"] = 500
            reply["content"] = json.dumps({"success": False, "error": str(exc)})

        return reply

    def do_nothing(self, values_dict, type_id):
        pass
