# Separate Platform Admin table instead of a role flag on Users

Platform operators and platform end-users are modelled as two tables (`platform_admins`, `users`) rather than one `users` table with a `role`/`is_admin` column. Admins are registered manually (seed script or direct SQL) and never flow through the Users CRUD lifecycle; Users are created by admins and carry their own credentials and status. Separate tables stop an admin from being listed, edited, or deleted through the user endpoints.

## Considered Options

- **`role`/`is_admin` column on `users`** — rejected: admins would share the Users CRUD surface, and the two lifecycles (manual admin registration vs. admin-driven user registration) would entangle.
