# iPhone authorization model

The iPhone app does not decide which leads a user may access. Authorization remains server-side in the Roof Brokers API.

- `OWNER`: may view all leads in the company and assign/reassign leads.
- Non-owner users: may view only leads whose `assigned_user_id` matches their authenticated user ID.
- User management and lead assignment are owner-only operations.
- The iOS app stores no CRM password, API token, owner reset code, or Railway credential in source.
- The WKWebView uses the backend's secure session/cookie authentication flow.

This separation is intentional so modifying or reverse-engineering the iPhone client cannot grant broader CRM access.
