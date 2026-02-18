#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# LogsOverReflector - Exposes Indigo event log as JSON API over Reflector
#
# Endpoints:
#   GET /message/com.simons-plugins.logs-over-reflector/log?lines=500&offset=0&source=X&search=Y
#   GET /message/com.simons-plugins.logs-over-reflector/sources
#   GET /message/com.simons-plugins.logs-over-reflector/history?date=YYYY-MM-DD&lines=500&offset=0&source=X&search=Y
#   GET /message/com.simons-plugins.logs-over-reflector/dates
#
try:
    import indigo
except ImportError:
    pass

import glob
import json
import os
import re


class Plugin(indigo.PluginBase):

    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs, **kwargs):
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs, **kwargs)
        self.debug = False

    def startup(self):
        self.logger.info("LogsOverReflector started")

    def shutdown(self):
        self.logger.info("LogsOverReflector stopped")

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

            # Fetch extra entries so we can detect whether more history exists.
            # Without filters: fetch offset + lines + 1 so we can see beyond the page.
            # With filters: multiply by 3 since many raw entries may be filtered out.
            fetch_count = (offset + line_count + 1) * (3 if has_filter else 1)
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
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
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

    def history(self, action, dev=None, caller_waiting_for_result=None):
        """Return historical event log entries from a dated log file.

        Query params:
            date   - date in YYYY-MM-DD format (required)
            lines  - number of entries to return (default 500, max 5000)
            offset - number of most-recent filtered entries to skip (for pagination)
            source - filter by source name
            search - text search in message field
        """
        reply = indigo.Dict()
        reply["headers"] = indigo.Dict({"Content-Type": "application/json"})

        try:
            props = dict(action.props)
            query_args = props.get("url_query_args", {})

            date_str = query_args.get("date", "").strip()
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                reply["status"] = 400
                reply["content"] = json.dumps({"success": False, "error": "Missing or invalid 'date' parameter (YYYY-MM-DD)"})
                return reply

            # Build log file path
            logs_dir = os.path.join(indigo.server.getInstallFolderPath(), "Logs")
            log_file = os.path.join(logs_dir, date_str + " Events.txt")

            if not os.path.isfile(log_file):
                reply["status"] = 200
                reply["content"] = json.dumps({"success": True, "count": 0, "totalFiltered": 0, "hasMore": False, "entries": []})
                return reply

            # Parse parameters
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

            source_filter = query_args.get("source", "").strip()
            search_filter = query_args.get("search", "").strip().lower()

            # Parse log file
            line_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\t+(\S.*?)\t+(.*)$")
            parsed_entries = []

            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                for raw_line in f:
                    raw_line = raw_line.rstrip("\n").rstrip("\r")
                    m = line_pattern.match(raw_line)
                    if m:
                        parsed_entries.append({
                            "timestamp": m.group(1),
                            "source": m.group(2),
                            "message": m.group(3),
                        })
                    elif parsed_entries:
                        # Continuation line — append to previous entry
                        parsed_entries[-1]["message"] += "\n" + raw_line

            # Apply filters
            filtered = []
            for entry in parsed_entries:
                if source_filter and entry["source"] != source_filter:
                    continue
                if search_filter and search_filter not in entry["message"].lower():
                    continue
                filtered.append({
                    "message": entry["message"],
                    "source": entry["source"],
                    "typeVal": 8,
                    "timestamp": entry["timestamp"],
                })

            # Apply pagination (same logic as log handler)
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

    def dates(self, action, dev=None, caller_waiting_for_result=None):
        """Return available log dates (dates that have log files)."""
        reply = indigo.Dict()
        reply["headers"] = indigo.Dict({"Content-Type": "application/json"})

        try:
            logs_dir = os.path.join(indigo.server.getInstallFolderPath(), "Logs")
            pattern = os.path.join(logs_dir, "* Events.txt")
            files = glob.glob(pattern)

            date_list = []
            for f in files:
                basename = os.path.basename(f)
                # Extract date from "YYYY-MM-DD Events.txt"
                if basename.endswith(" Events.txt"):
                    date_part = basename[:-len(" Events.txt")]
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_part):
                        date_list.append(date_part)

            date_list.sort(reverse=True)

            result = {"dates": date_list}
            reply["status"] = 200
            reply["content"] = json.dumps(result, indent=None)

        except Exception as exc:
            self.logger.exception(exc)
            reply["status"] = 500
            reply["content"] = json.dumps({"success": False, "error": str(exc)})

        return reply

    def do_nothing(self, values_dict, type_id):
        pass
