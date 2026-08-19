# SQLModel for tables, separate Pydantic DTOs for the API

We use SQLModel only to define database tables. API request/response types are separate Pydantic models; table models never cross the API boundary. SQLModel's table-plus-validation merge is convenient, but reusing a table model as a request/response schema couples the database shape to the wire format, so we keep them apart.
