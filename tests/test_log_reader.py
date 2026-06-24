"""Tests for core/log_reader.py — XML parsing and time conversion helpers."""

import unittest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from core.log_reader import (
    _parse_iso_time,
    _parse_event_xml,
    EVT_LEVEL_MAP,
    CLASSIC_LOGS,
    EVENT_TYPE_MAP,
    WARSAW_TZ,
)

# A realistic Windows Event Log XML snippet for an Error event
ERROR_XML = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Service Control Manager" Guid="{ceb3e4b1-1c7e-4d9a-8a5e-9b0f1e2c3d4a}" />
    <EventID>7036</EventID>
    <Version>0</Version>
    <Level>2</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8080000000000000</Keywords>
    <TimeCreated SystemTime="2026-06-24T12:00:00.000000Z" />
    <EventRecordID>12345</EventRecordID>
    <Channel>System</Channel>
    <Computer>DESKTOP-ABC123</Computer>
    <Security />
  </System>
  <EventData>
    <Data Name="param1">Windows Update</Data>
    <Data Name="param2">Stopped</Data>
  </EventData>
</Event>"""

# A Warning event
WARNING_XML = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Disk" />
    <EventID>153</EventID>
    <Version>0</Version>
    <Level>3</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8000000000000000</Keywords>
    <TimeCreated SystemTime="2026-06-24T10:30:00.000000Z" />
    <EventRecordID>12346</EventRecordID>
    <Channel>System</Channel>
    <Computer>DESKTOP-ABC123</Computer>
    <Security />
  </System>
  <EventData>
    <Data Name="Message">Disk space is low</Data>
  </EventData>
</Event>"""

# Event XML with UserData instead of EventData
USERDATA_XML = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="User32" />
    <EventID>1074</EventID>
    <Version>0</Version>
    <Level>2</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8000000000000000</Keywords>
    <TimeCreated SystemTime="2026-06-24T08:00:00.000000Z" />
    <EventRecordID>12347</EventRecordID>
    <Channel>System</Channel>
    <Computer>DESKTOP-ABC123</Computer>
    <Security />
  </System>
  <UserData>
    <Shutdown>
      <Reason>Reboot</Reason>
      <Comment>System update</Comment>
    </Shutdown>
  </UserData>
</Event>"""


class TestParseIsoTime(unittest.TestCase):
    """Tests for _parse_iso_time()."""

    def test_utc_zulu(self):
        """ISO time ending with Z should be parsed and converted to Warsaw time."""
        result = _parse_iso_time("2026-06-24T12:00:00.0000000Z")
        self.assertIsNotNone(result)
        # Warsaw is UTC+2 in June (summer time)
        expected_offset = timedelta(hours=2)
        self.assertEqual(result.utcoffset(), expected_offset)
        self.assertEqual(result.hour, 14)  # 12:00 UTC → 14:00 Warsaw

    def test_with_offset(self):
        """ISO time with explicit offset should be parsed."""
        result = _parse_iso_time("2026-06-24T10:00:00+00:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 12)  # 10:00 UTC → 12:00 Warsaw

    def test_with_positive_offset(self):
        """ISO time with +02:00 offset should be parsed."""
        result = _parse_iso_time("2026-06-24T15:00:00+02:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 15)  # Already in Warsaw time

    def test_invalid_string(self):
        """An unparseable string should return None."""
        result = _parse_iso_time("not-a-date")
        self.assertIsNone(result)

    def test_empty_string(self):
        """An empty string should return None."""
        result = _parse_iso_time("")
        self.assertIsNone(result)


class TestParseEventXml(unittest.TestCase):
    """Tests for _parse_event_xml()."""

    def test_parses_error_event(self):
        """An Error (Level=2) XML should produce a correct event dict."""
        event = _parse_event_xml(ERROR_XML, "System")
        self.assertIsNotNone(event)
        self.assertEqual(event["SourceName"], "Service Control Manager")
        self.assertEqual(event["EventID"], 7036)
        self.assertEqual(event["Level"], "Error")
        self.assertEqual(event["EventType"], 2)
        self.assertEqual(event["LogSource"], "System")

    def test_parses_warning_event(self):
        """A Warning (Level=3) XML should produce a correct event dict."""
        event = _parse_event_xml(WARNING_XML, "System")
        self.assertIsNotNone(event)
        self.assertEqual(event["SourceName"], "Disk")
        self.assertEqual(event["EventID"], 153)
        self.assertEqual(event["Level"], "Warning")
        self.assertEqual(event["EventType"], 3)

    def test_extracts_eventdata(self):
        """EventData with named Data elements should be extracted into the message."""
        event = _parse_event_xml(ERROR_XML, "System")
        self.assertIsNotNone(event)
        self.assertIn("param1", event["Message"])
        self.assertIn("Windows Update", event["Message"])
        self.assertIn("param2", event["Message"])
        self.assertIn("Stopped", event["Message"])

    def test_extracts_userdata(self):
        """UserData (fallback when EventData is missing) should be extracted."""
        event = _parse_event_xml(USERDATA_XML, "System")
        self.assertIsNotNone(event)
        self.assertEqual(event["SourceName"], "User32")
        self.assertEqual(event["EventID"], 1074)
        # UserData should produce some text content
        self.assertTrue(len(event["Message"]) > 0)

    def test_invalid_xml(self):
        """Invalid XML should return None."""
        event = _parse_event_xml("not xml", "System")
        self.assertIsNone(event)

    def test_empty_string(self):
        """Empty string XML should return None."""
        event = _parse_event_xml("", "System")
        self.assertIsNone(event)

    def test_missing_system_node(self):
        """XML without a System node should return None."""
        xml = "<Event><EventData><Data>foo</Data></EventData></Event>"
        event = _parse_event_xml(xml, "System")
        self.assertIsNone(event)

    def test_time_converted_to_warsaw(self):
        """TimeGenerated should be converted to Europe/Warsaw timezone."""
        event = _parse_event_xml(ERROR_XML, "System")
        self.assertIsNotNone(event)
        self.assertEqual(event["TimeGenerated"].tzinfo, WARSAW_TZ)
        self.assertEqual(event["TimeGenerated"].hour, 14)  # 12:00 UTC → 14:00 Warsaw

    def test_unknown_level_mapped_gracefully(self):
        """An unknown Level value should produce 'Unknown (N)' string."""
        xml = ERROR_XML.replace("<Level>2</Level>", "<Level>99</Level>")
        event = _parse_event_xml(xml, "System")
        self.assertIsNotNone(event)
        self.assertIn("Unknown", event["Level"])

    def test_missing_provider_name(self):
        """XML without a Provider Name attribute should use 'Unknown'."""
        xml = ERROR_XML.replace('Name="Service Control Manager" ', "")
        event = _parse_event_xml(xml, "System")
        self.assertIsNotNone(event)
        self.assertEqual(event["SourceName"], "Unknown")

    def test_fallback_channel(self):
        """When Channel element is missing, the provided channel name should be used."""
        xml = ERROR_XML.replace("<Channel>System</Channel>", "")
        event = _parse_event_xml(xml, "FallbackChannel")
        self.assertIsNotNone(event)
        self.assertEqual(event["LogSource"], "FallbackChannel")


class TestConstants(unittest.TestCase):
    """Tests for module-level constants."""

    def test_evt_level_map_has_critical(self):
        """EVT_LEVEL_MAP should map level 1 to 'Critical'."""
        self.assertEqual(EVT_LEVEL_MAP[1], "Critical")

    def test_evt_level_map_has_error(self):
        """EVT_LEVEL_MAP should map level 2 to 'Error'."""
        self.assertEqual(EVT_LEVEL_MAP[2], "Error")

    def test_evt_level_map_has_warning(self):
        """EVT_LEVEL_MAP should map level 3 to 'Warning'."""
        self.assertEqual(EVT_LEVEL_MAP[3], "Warning")

    def test_evt_level_map_has_information(self):
        """EVT_LEVEL_MAP should map level 4 to 'Information'."""
        self.assertEqual(EVT_LEVEL_MAP[4], "Information")

    def test_evt_level_map_has_verbose(self):
        """EVT_LEVEL_MAP should map level 5 to 'Verbose'."""
        self.assertEqual(EVT_LEVEL_MAP[5], "Verbose")

    def test_classic_logs(self):
        """CLASSIC_LOGS should contain the four standard Windows logs."""
        self.assertIn("Application", CLASSIC_LOGS)
        self.assertIn("Security", CLASSIC_LOGS)
        self.assertIn("Setup", CLASSIC_LOGS)
        self.assertIn("System", CLASSIC_LOGS)

    def test_event_type_map_has_error(self):
        """EVENT_TYPE_MAP should map the error constant."""
        import win32evtlog
        self.assertIn(win32evtlog.EVENTLOG_ERROR_TYPE, EVENT_TYPE_MAP)

    def test_event_type_map_has_warning(self):
        """EVENT_TYPE_MAP should map the warning constant."""
        import win32evtlog
        self.assertIn(win32evtlog.EVENTLOG_WARNING_TYPE, EVENT_TYPE_MAP)


if __name__ == "__main__":
    unittest.main()
