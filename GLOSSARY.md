# Invicta bus-priority proposals

Invicta explores changes that help buses meet their schedules while accounting for passengers and other people using the affected streets.

## Language

**Line**:
A numbered bus route, including its directions and the scheduled trips that serve them. A line can include trips that serve only part of its route.
_Avoid_: Corridor, trip

**Direction**:
An ordered route and stop sequence towards a destination. The two directions of a line can use different streets and stops.
_Avoid_: Reversed route

**Trip**:
One scheduled bus journey in a direction. A trip can start or finish before the endpoints of the full line.
_Avoid_: Line, direction

**Focus section**:
A continuous range between two stops in one direction, selected for closer review within the context of the whole line.
_Avoid_: Simulation coverage

**Simulation coverage**:
The geographic extent, direction, time period and conditions represented by a particular simulation. Showing a section of the line on a map does not establish simulation coverage there.
_Avoid_: Whole line, focus section
