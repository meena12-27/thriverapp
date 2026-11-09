# Thriver system architecture

```mermaid
flowchart LR
    Driver([Driver]) --> App["Flutter app<br/>(web / Android)"]
    Admin([Operator]) --> Dash["Admin dashboard<br/>(HTML + JS)"]
    App -->|REST + JWT| API
    Dash -->|REST + JWT| API

    subgraph Backend["FastAPI backend"]
        API["Routes<br/>auth, parking, reservations, admin"]
        API --> Rec["Recommendation service<br/>weighted score, hard filters"]
        API --> Fc["Forecast service<br/>recent-trend extrapolation"]
        API --> Res["Reservation service<br/>5-min hold, lazy expiry"]
        Rec --> Fc
    end

    API --> DB[("PostgreSQL<br/>malls, slots, users, reservations,<br/>history, slot_activity")]
    Sim["Sensor simulator<br/>(Python)"] -->|slot changes + events| DB
    Fc -.->|reads recent events| DB
```

## Components

- **Flutter app**: map, recommendation, forecast, reservations, history.
- **Admin dashboard**: static HTML/JS served by the API at `/admin-dashboard/`.
- **FastAPI backend**: thin routes over pure service functions (recommendation, forecast), so the logic is unit tested without a database.
- **PostgreSQL**: source of truth. `slot_activity` is an event log that feeds both the admin feed and the forecast.
- **Simulator**: stands in for parking sensors by flipping slots and logging events.
