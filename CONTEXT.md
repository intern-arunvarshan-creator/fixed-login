# Platform Admin

Backend for platform operators to manage the platform's users. Two kinds of people exist: **Users** (the managed) and **Platform Admins** (the operators who log in).

## Language

**User**:
A person who uses the platform, whose account is created and managed through this backend by a Platform Admin.
_Avoid_: Customer, member, account, end-user

**Platform Admin**:
A person who operates this backend — logs in and manages Users. Registered manually (seed script or direct SQL), never through the API.
_Avoid_: Admin, root user, operator, superuser, staff

**Current Admin**:
The authenticated Platform Admin making the current request, resolved from the access token.
_Avoid_: Current user, requester, principal

**Audit Entry**:
One row in the audit log recording a single Platform Admin action (a User mutation or an authentication attempt). Append-only.
_Avoid_: Audit record, log line, history item
