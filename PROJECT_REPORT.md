# BuildBid: A Web-Based Construction Project Bidding Platform

**Course:** [COURSE NAME]
**Author:** [YOUR NAME]
**Submission Date:** [DATE]

---

## 1. Abstract

BuildBid is a web-based platform that connects construction clients with
contractors through an open bidding model. Clients post projects with a
budget range, location and deadline, while verified contractors submit
competing bids that the client can compare side-by-side and award. The
system also tracks the project from award through to client-confirmed
completion, and closes the loop with a one-time client review that updates
the contractor's running average rating. The platform is implemented as a
Django 6.0 application with a role-based custom user model, server-rendered
HTML templates styled with Tailwind CSS, and a relational database backend
(SQLite for development, MySQL optional in production). This report documents
the requirements, design, implementation and testing of the platform.

## 2. Introduction

In the local construction market, clients who want a small or medium build
job done often rely on personal contacts to find a contractor, which makes
price comparison difficult and gives clients no neutral signal of past work
quality. Contractors, on the other hand, struggle to discover new work
outside their existing network. BuildBid addresses both sides of this gap
with a single platform: clients describe what they need, multiple
contractors bid, the client picks one, and the resulting work is tied to a
public rating that grows over time. This report walks through the design
and implementation of that platform, with a focus on the role-based
workflow that drives the state of every project from posting to review.

## 3. Project Scope and Objectives

The scope of BuildBid is a single web application covering the project
lifecycle from posting to review. It does **not** include in-app messaging,
payments, dispute resolution, or contractor-side scheduling tools.

Objectives:

- Provide separate registration and dashboards for clients and contractors.
- Let clients post, browse and filter construction projects.
- Let verified contractors submit one bid per project, with amount and
  proposed timeline.
- Let clients compare bids side-by-side and award exactly one.
- Track each project through Open → In Progress → Completed, with a
  client-side confirmation step before the review is unlocked.
- Capture a 1–5 star review per project and maintain a running average
  rating on every contractor's profile.
- Restrict admin operations (contractor verification, category management)
  to staff users via the built-in Django admin site.

## 4. Requirements Analysis

### 4.1 Functional Requirements

| ID    | Requirement                                                                 |
|-------|-----------------------------------------------------------------------------|
| FR-01 | A visitor can register as either a Client or a Contractor.                  |
| FR-02 | A contractor registration must capture company name and years of experience and start in a Pending verification state. |
| FR-03 | A registered user can log in, log out and edit their profile.               |
| FR-04 | A client can post a project with title, description, category, location, budget range and deadline. |
| FR-05 | Anyone can browse the list of Open projects, filtered by category, location and budget. |
| FR-06 | A verified contractor can submit at most one bid per project, with bid amount and proposed timeline in days. |
| FR-07 | A client can view all bids on their own project sorted by amount, and award exactly one bid. |
| FR-08 | Awarding a bid moves the project from Open to In Progress and rejects all other bids. |
| FR-09 | The awarded contractor can mark an In Progress project as Completed.        |
| FR-10 | The client must explicitly confirm completion before a review can be left.  |
| FR-11 | After confirmation, the client can leave exactly one review (1–5 stars + optional comment). |
| FR-12 | A new review updates the contractor's average rating shown on their profile. |
| FR-13 | A staff admin can mark a contractor as Verified or Rejected via the Django admin site. |

### 4.2 Non-Functional Requirements

| ID     | Category         | Requirement                                                        |
|--------|------------------|--------------------------------------------------------------------|
| NFR-01 | Security         | Passwords must use Django's built-in PBKDF2 hashing and the default password validators. |
| NFR-02 | Security         | Role-restricted views must return 403 to a logged-in user with the wrong role. |
| NFR-03 | Security         | Users must not be able to self-register with the ADMIN role.       |
| NFR-04 | Security         | All state-changing actions must be protected by CSRF tokens.       |
| NFR-05 | Data integrity   | A unique database constraint must enforce one bid per contractor per project. |
| NFR-06 | Usability        | Pages must render on both desktop and mobile widths via a Tailwind utility stylesheet. |
| NFR-07 | Maintainability  | Each domain area (accounts, projects, bids, reviews) lives in its own Django app with its own models, views, forms, URLs and tests. |
| NFR-08 | Portability      | The database backend must be swappable between SQLite and MySQL via environment variables, with no code changes. |
| NFR-09 | Performance      | Project listings must be paginated (10 per page) and join related rows in a single query (`select_related`). |

## 5. Implementation Modules

The application is split into four Django apps, each owning its slice of
the domain. The dependency direction is one-way: `projects` depends on
`accounts`; `bids` and `reviews` depend on both.

### 5.1 `accounts` — Identity, Roles and Contractor Profiles

This module defines the custom `User` model (with `CLIENT`, `CONTRACTOR`
and `ADMIN` role choices) and the one-to-one `ContractorProfile` that
holds company name, experience, license document, verification status and
the cached average rating. It implements registration, login, logout,
role-aware dashboards, the public contractor detail page and the
`role_required` decorator that gates every role-restricted view in the
rest of the project.

### 5.2 `projects` — Project Posting, Browsing and Lifecycle

This module owns the `Project` model and the `ProjectCategory` lookup
table, and is the source of truth for project state (Open → In Progress
→ Completed → Cancelled). It implements project creation (clients only),
the filterable and paginated public project list, the project detail
page, and the two endpoints that drive the completion handshake
(`mark_completed` for the contractor and `confirm_completion` for the
client).

### 5.3 `bids` — Bid Submission and Awarding

This module defines the `Bid` model with a unique constraint enforcing
one bid per contractor per project. It implements bid submission by
verified contractors and the `award_bid` endpoint, which atomically
accepts one bid, rejects every other bid on the project, assigns the
awarded contractor and moves the project to In Progress.

### 5.4 `reviews` — Post-Project Ratings

This module defines the `Review` model (one-to-one with `Project`, with a
1–5 rating and optional comment) and the `review_create` view that lets a
client leave a review on a project that is both Completed *and*
client-confirmed. On save it triggers `ContractorProfile.recalculate_rating()`
so the contractor's public average updates immediately.

## 6. System Architecture and Design

BuildBid follows Django's MTV (Model–Template–View) pattern. There is no
separate REST layer — views render server-side HTML templates directly.
All pages are styled with Tailwind CSS utility classes from a single
project-wide stylesheet, and user-uploaded files (profile pictures,
license documents) are served from `MEDIA_ROOT` during development.

```
+---------------------------------------------------------------+
|                          Browser                              |
|   (server-rendered HTML + Tailwind CSS + minimal JS)          |
+----------------------------+----------------------------------+
                             |  HTTP (forms, CSRF)
                             v
+---------------------------------------------------------------+
|                    Django URL Dispatcher                      |
+----+-------------+-------------+-------------+----------------+
     |             |             |             |
     v             v             v             v
+---------+   +----------+   +-------+   +---------+
| accounts|   | projects |   | bids  |   | reviews |
| views   |   | views    |   | views |   | views   |
+----+----+   +-----+----+   +---+---+   +----+----+
     |              |           |             |
     +------+-------+-----+-----+------+------+
            |             |            |
            v             v            v
+---------------------------------------------------------------+
|                       Django ORM                              |
+---------------------------------------------------------------+
                             |
                             v
+---------------------------------------------------------------+
|         Relational DB  (SQLite default / MySQL optional)      |
+---------------------------------------------------------------+
```

The dependency graph between apps is intentionally acyclic:

```
              +-----------+
              | accounts  |
              +-----+-----+
                    ^
                    |
              +-----+-----+
              | projects  |
              +-----+-----+
                ^       ^
                |       |
        +-------+       +-------+
        |                       |
  +-----+-----+           +-----+-----+
  |   bids    |           |  reviews  |
  +-----------+           +-----------+
```

`projects` imports from `accounts` (the user model and the role decorator);
`bids` and `reviews` both import `Project` and the role decorator. Nothing
imports the other direction, which keeps `accounts` re-usable.

## 7. Database Design

The schema is implemented as Django models, which generate the underlying
relational tables. The core entities and relationships are:

```
+----------------+        +-----------------------+
|     User       |1------1|   ContractorProfile   |
|----------------|        |-----------------------|
| id (PK)        |        | id (PK)               |
| username       |        | user_id (FK,UQ)       |
| email          |        | company_name          |
| role           |        | experience_years      |
| phone_number   |        | license_number        |
| address        |        | license_document      |
| profile_picture|        | biography             |
| password (hash)|        | verification_status   |
+----------------+        | rating_average        |
   1 |       1 |          +-----------------------+
     |         |
     |client   |awarded_contractor
     v         v
+----------------+        +-----------------+
|    Project     |* ----1 | ProjectCategory |
|----------------|        |-----------------|
| id (PK)        |        | id (PK)         |
| client_id  (FK)|        | name (UQ)       |
| awarded_contr- |        | description     |
|   actor_id (FK)|        +-----------------+
| category_id(FK)|
| title          |
| description    |
| location       |
| budget_min     |
| budget_max     |
| deadline       |
| status         |
| completion_    |
|   confirmed    |
| created_at     |
+----------------+
  1 |        1 |
    | *        | 1
    v          v
+-----------+  +----------+
|   Bid     |  |  Review  |
|-----------|  |----------|
| id (PK)   |  | id (PK)  |
| project_id|  | project_ |
|   (FK)    |  |   id(FK, |
| contractor|  |    UQ)   |
|   _id (FK)|  | client_id|
| bid_amount|  | contract-|
| proposed_ |  |  or_id   |
|  timeline_|  | rating   |
|  days     |  | comment  |
| status    |  | created_ |
| submitted_|  |  at      |
|  at       |  +----------+
+-----------+
UNIQUE(project_id, contractor_id)
```

Notable constraints:

- `Bid` carries a composite `UNIQUE(project_id, contractor_id)` constraint
  (`unique_bid_per_contractor`) so the database itself rejects a second bid
  from the same contractor on the same project.
- `Review.project` is a `OneToOneField`, enforcing one review per project.
- `Project.category` uses `on_delete=PROTECT` to prevent accidental deletion
  of a category that still has projects.
- `Project.awarded_contractor` is nullable and `on_delete=SET_NULL`, so a
  contractor account closure does not destroy the historical project record.

## 8. Tools and Technologies

| Layer                | Choice                                                |
|----------------------|-------------------------------------------------------|
| Language             | Python 3                                              |
| Web framework        | Django 6.0.5                                          |
| Database (dev)       | SQLite                                                |
| Database (optional)  | MySQL (via `DB_ENGINE=mysql` + `mysqlclient`)         |
| Templating           | Django templates                                      |
| Styling              | Tailwind CSS (via `tailwind.config.js`, `package.json`) |
| Image handling       | Pillow 12.x                                           |
| Auth                 | Django's built-in `AbstractUser` + PBKDF2 hashing     |
| Admin tooling        | Django admin (for verification, category management) |
| Version control      | Git                                                   |
| Editor / runtime     | Local development on Windows 11                       |

## 9. Methodology

Development followed an incremental, feature-by-feature approach. Each
feature slice was implemented end-to-end (model → migration → form → view
→ template → test) before the next was started. The git history records
this progression as a chain of focused commits:

1. `feat(accounts)` — custom user, contractor profiles, auth flows.
2. `feat(projects)` — project posting, browsing and the completion handshake.
3. `feat(bids)` — bid submission, comparison and awarding.
4. `feat(reviews)` — ratings and review-driven average updates.

Each new app was added to `INSTALLED_APPS`, given its own URL include and
its own test module, and verified with `python manage.py test` before the
next slice began. Defensive `getattr(..., related_name, None)` checks in
the earlier views (see `projects/views.py:64`, `accounts/views.py:96`)
let those views run even when downstream apps had not yet been added — a
small detail that made the incremental build order practical.

## 10. Testing

Each app ships with its own `tests.py`. The `accounts` test module
(`accounts/tests.py`) is the most developed and exercises the central
security and routing rules of the system:

| Test                                            | What it verifies                                                                 |
|-------------------------------------------------|----------------------------------------------------------------------------------|
| `test_client_registration_creates_client`       | Registering with role=CLIENT creates a User with the CLIENT role and redirects to the dashboard. |
| `test_contractor_registration_creates_pending_profile` | Contractor registration also creates a `ContractorProfile` in the PENDING state.       |
| `test_admin_role_cannot_be_self_selected`       | Posting `role=ADMIN` to the registration view does not create a user (NFR-03).   |
| `test_anonymous_redirected_to_login`            | The dashboard is `login_required`.                                               |
| `test_client_sees_client_dashboard`             | A logged-in client lands on `accounts/dashboard_client.html`.                    |

Tests are run with `python manage.py test`, which Django executes against
a throwaway test database so production data is untouched. In addition to
the automated tests, the workflow was exercised manually end-to-end —
register a client, post a project, register and admin-verify a
contractor, submit a bid, award it, mark the project completed, confirm
completion, and leave a review — to validate the full state machine in a
browser.

## 11. Results and Discussion

The finished platform meets every functional requirement listed in
Section 4.1. A client can post a project in under a minute, a verified
contractor can submit a bid in a few clicks, and the client sees every
competing bid on a single page sorted by amount. The completion-and-review
handshake is the part of the system that demanded the most thought: the
naive design (contractor marks complete → review unlocked) hands the
contractor unilateral control over their own rating cycle, so the final
design splits it into a two-step handshake (`mark_completed` →
`confirm_completion` → review) where the client retains the final word.
The unique constraint on `(project, contractor)` proved its worth during
manual testing — without it, a double-submitted form could otherwise have
created two bids by the same contractor on the same project.

## 12. Limitations

- **No in-app messaging.** A client cannot ask a bidder a clarifying
  question through the platform; they have to fall back to phone or email
  contact details on the contractor profile.
- **No payments.** The system does not process or even record any monetary
  transaction; the bid amount is purely a quoted figure.
- **No notifications.** A contractor only learns they have been awarded a
  project by visiting the dashboard or the project page.
- **No file attachments on projects.** A client cannot attach drawings,
  blueprints or photos to a project description.
- **Manual contractor verification.** Verification is a human decision
  taken in the Django admin site; there is no automated KYC.
- **No public API.** All interaction is via server-rendered HTML; a mobile
  app or third-party integration would require an additional API layer.

## 13. Future Work

- Add a REST API (Django REST Framework) so a mobile client could be built
  on the same data model.
- Add in-app messaging between the client and each bidder, scoped to the
  project.
- Add file attachments on projects (drawings, site photos) and on bid
  submissions (method statements).
- Add email or SMS notifications for the key state transitions (new bid
  on your project, bid awarded, project marked complete, review received).
- Add dispute / cancellation flows with an audit trail.
- Add an escrow-style payment integration so funds are released only on
  client confirmation of completion.
- Add search ranking on the contractor directory (by rating, completed
  jobs, location).

## 14. Conclusion

BuildBid demonstrates that a focused, role-based bidding workflow for the
construction sector can be built on a small, well-organised Django code
base. The four-app split (`accounts`, `projects`, `bids`, `reviews`) maps
cleanly onto the four phases of the user journey — identity, posting,
bidding, and review — and the database-level constraints together with
the `role_required` decorator keep the security model simple to reason
about. The result is a working platform that closes the loop from project
posting to public rating, and a foundation that could realistically be
extended with messaging, payments and a mobile client.

## 15. References

1. Django Software Foundation, *Django documentation*, version 6.0,
   https://docs.djangoproject.com/en/6.0/
2. Django Software Foundation, *Customizing authentication in Django*,
   https://docs.djangoproject.com/en/6.0/topics/auth/customizing/
3. Tailwind Labs, *Tailwind CSS documentation*,
   https://tailwindcss.com/docs
4. Python Software Foundation, *The Python Language Reference, Release 3*,
   https://docs.python.org/3/reference/
5. Oracle Corporation, *MySQL 8.0 Reference Manual*,
   https://dev.mysql.com/doc/refman/8.0/en/
