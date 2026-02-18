#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Log API - Exposes Indigo event log as JSON API
#
# Endpoints:
#   GET /message/com.simons-plugins.indigo-log-api/log?lines=500&offset=0&source=X&search=Y
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
        """Return event log entries as JSON with pagination.

        Query params:
            lines  - number of entries to return (default from plugin config)
            offset - number of most-recent filtered entries to skip (for pagination)
            source - filter by TypeStr (plugin source name)
            search - text search in Message field
        """
        reply = indigo.Dict()
        reply["headers"] = indigo.Dict({"Content-Type": "application/json"})

        try:
            props = dict(action.props)
            query_args = props.get("url_query_args", {})

            # Parse line count and offset
            default_lines = int(self.pluginPrefs.get("defaultLineCount", 500))
            try:
                line_count = int(query_args.get("lines", default_lines))
            except (ValueError, TypeError):
                line_count = default_lines
            line_count = max(1, min(line_count, 5000))

            try:
                offset = int(query_args.get("offset", 0))
            except (ValueError, TypeError):
                offset = 0
            offset = max(0, offset)

            # Fetch enough raw entries to cover offset + requested lines.
            # With filters active, we may need more raw entries than offset + lines
            # to fill the page, so fetch a generous amount.
            source_filter = query_args.get("source", "").strip()
            search_filter = query_args.get("search", "").strip().lower()
            has_filter = bool(source_filter or search_filter)

            # When filtering, fetch more raw entries to ensure we can fill the page
            fetch_count = (offset + line_count) * (3 if has_filter else 1)
            fetch_count = min(fetch_count, 10000)

            raw_entries = indigo.server.getEventLogList(
                returnAsList=True,
                showTimeStamp=True,
                lineCount=fetch_count,
            )

            # Build filtered entries list (chronological: oldest first)
            filtered = []
            for entry in raw_entries:
                entry_dict = dict(entry)
                message = entry_dict.get("Message", "")
                source = entry_dict.get("TypeStr", "")
                type_val = entry_dict.get("TypeVal", 0)
                timestamp = entry_dict.get("TimeStamp", "")

                if source_filter and source != source_filter:
                    continue
                if search_filter and search_filter not in message.lower():
                    continue

                filtered.append({
                    "message": message,
                    "source": source,
                    "typeVal": type_val,
                    "timestamp": str(timestamp),
                })

            # Apply pagination: skip the most recent `offset` entries,
            # then return up to `lines` entries from the older end
            total_filtered = len(filtered)
            if offset >= total_filtered:
                entries = []
            else:
                end_index = total_filtered - offset
                start_index = max(0, end_index - line_count)
                entries = filtered[start_index:end_index]

            has_more = (total_filtered - offset - len(entries)) > 0

            result = {
                "success": True,
                "count": len(entries),
                "totalFiltered": total_filtered,
                "hasMore": has_more,
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
