# NOAA storm mapping

Open **Field Map → NOAA Storms**, choose a storm day and Hail, Wind, or Tornado,
then select **Load reports**. Reports appear over the existing property map.
Pan/zoom to see the number in view, or select **Show all loaded reports**.
Selecting a marker shows location, event time in the device's timezone,
reported magnitude, and NOAA comments. **Open NOAA source CSV** links to the
original data. **Clear layer** removes only NOAA report markers.

An SPC storm day runs from noon UTC on the selected date through noon UTC the
next day. Before noon UTC the default is the previous calendar date. Available
dates begin June 1, 1999. Hail sizes are converted from hundredths of an inch;
wind speeds are shown in knots. Unknown values remain unknown.

Source: https://www.spc.noaa.gov/climo/reports/ (NOAA/NWS Storm Prediction Center).
These preliminary point reports can be revised. They are not a hail swath,
proof of damage at a property, or contractor ground verification. The existing
MRMS MESH radar overlay and Ground Evidence layer remain independent.
Loading NOAA reports does not create leads or send anything to AccuLynx.

The authenticated server fetches NOAA data and caches successful responses for
five minutes (up to 128 date/type combinations per process). Failed upstream
requests and malformed responses produce an error, not an empty storm day.
If a reload fails, the map explicitly identifies the previously loaded data.
NOAA report loading requires connectivity; existing offline visit queues are
unchanged.

Build integration follows the repository's runtime-patch packaging in
`.staging/storm_mapping37`, applied after the owner-assignment patch.

Validation: `python tests/storm_mapping_runtime.py` inside the built container;
`node tests/storm_mapping_ui.cjs` from the repository root.
