# BuildBid — Short Project Report

**Course:** [COURSE NAME]
**Author:** [YOUR NAME]
**Date:** [DATE]

## 1. Abstract

BuildBid is a Django web app where clients post construction jobs and
contractors bid on them. The client picks one bid, the work is tracked
through to completion, and then the client leaves a star rating that
shows up on the contractor's public profile. It is built with Django 6
and Tailwind CSS, with SQLite for local development and an option to
switch to MySQL through environment variables. This short report covers
what the app does, how it is built, and what is still missing.

## 2. Introduction

Most small construction jobs around here still get assigned by word of
mouth. Clients don't compare quotes properly and contractors only get
work from people who already know them. I built BuildBid as a small
platform to fix both sides of that. A client describes the job, a few
contractors quote, the client picks one, and the result feeds back into
a public rating. The whole thing is a Django site with role-based
dashboards.

## 3. Project Scope and Objectives

The scope is one web app that covers the full life of a project: posting,
bidding, awarding, completion, and a review at the end. It does not do
payments, messaging or scheduling. The goals were:

- Two kinds of users, clients and contractors, with their own dashboards.
- Clients can post a project with a budget range, location and deadline.
- Verified contractors can submit one bid per project.
- Clients can compare bids and award one.
- Track each project through Open, In Progress and Completed.
- After completion is confirmed by the client, let them leave a rating
  that updates the contractor's average.
- Keep admin tasks (like verifying a contractor) in the Django admin site,
  not in the public app.

## 4. Requirements Analysis

The functional side is pretty much the user journey. A visitor can sign
up as a client or a contractor. Contractor sign-up takes company name
and years of experience, and the account starts as Pending. Anyone can
log in and edit their profile. Clients can post projects and browse the
open ones with filters for category, location and budget. A verified
contractor can bid on a project once with an amount and a timeline in
days. The client of that project can see every bid sorted by amount and
award one. Awarding moves the project to In Progress and rejects all the
other bids automatically. The awarded contractor then marks the work
completed when they are done, the client has to confirm it, and only
then can the client leave a 1 to 5 star review. That review updates the
contractor's average rating on their public profile. Verification of new
contractors is done by a staff admin from the Django admin site.

For non-functional stuff: passwords go through Django's built-in hashing
and validators, role-restricted views return 403 to the wrong role,
nobody can self-register as ADMIN, CSRF is on for all form posts, and a
unique database constraint stops a contractor from bidding twice on the
same project. The pages use Tailwind so they work on phone widths too.
The project listing is paginated. Each domain area lives in its own
Django app, and the database can be swapped between SQLite and MySQL
without code changes.

## 5. Implementation Modules

### 5.1 `accounts`

This app has the custom `User` model with three role choices and the
`ContractorProfile` that stores company info, verification status and
the cached average rating. It also has the `role_required` decorator
that every other app uses to gate views.

### 5.2 `projects`

This app owns the `Project` model and the category list, and runs the
project state machine. It implements posting, the filterable project
list with pagination, and the two endpoints for the completion
handshake.

### 5.3 `bids`

This app has the `Bid` model with the unique constraint that prevents
duplicate bids. It handles bid submission and the `award_bid` view,
which accepts one bid, rejects the rest, and moves the project to In
Progress, all in one transaction.

### 5.4 `reviews`

This app has the `Review` model, which is one-to-one with `Project` and
holds the 1 to 5 rating. After a review is saved it calls
`recalculate_rating()` on the contractor profile so the public average
updates straight away.

## 6. System Architecture and Design

The architecture is plain Django MTV. Browsers hit URLs, the URL
dispatcher sends each request to a view in one of the four apps, the
view talks to the ORM, and a template renders the HTML back. There is
no separate REST API. The four apps depend on each other in one
direction only: `projects` uses `accounts`, and `bids` and `reviews`
both use `accounts` and `projects`. Nothing imports the other way.

```
Browser  ->  URL dispatcher  ->  app views (accounts/projects/bids/reviews)
                                      ->  Django ORM  ->  DB
```

## 7. Database Design

There are six tables behind the four models. `User` has a one-to-one
link to `ContractorProfile`. `Project` belongs to a client (User), to a
`ProjectCategory`, and optionally to an awarded contractor (User again).
A `Bid` belongs to a `Project` and a contractor, with a composite unique
constraint on those two columns. A `Review` is one-to-one with `Project`
and keeps the client and contractor IDs alongside the rating and
comment. Category deletion is blocked while it has projects, and an
awarded contractor account can be deleted without destroying the
project history because that foreign key is set-null.

## 8. Tools and Technologies

Python 3 with Django 6.0.5 for the framework. Pillow for image uploads.
Tailwind CSS for the styling, pulled in through a small `package.json`
and `tailwind.config.js`. SQLite during development and MySQL as an
optional swap-in. The git repo tracks everything and the work was done
on Windows 11.

## 9. Methodology

I built the app one slice at a time. Each slice was one Django app,
finished end to end before the next one started: model, migration, form,
view, template, then tests. The commit history follows that order:
accounts first, then projects, then bids, then reviews. Early views in
`projects` and `accounts` guard against the later apps not existing yet
with simple `getattr` checks, which made the incremental order
practical.

## 10. Testing

The main tests live in `accounts/tests.py`. They check that a client
sign-up creates a CLIENT user, a contractor sign-up creates a
contractor with a Pending profile, that you cannot self-register as
ADMIN, that the dashboard redirects anonymous users to login, and that
a logged-in client lands on the client dashboard template. Tests run
with `python manage.py test`. I also manually walked the whole flow in
a browser, from registering both kinds of users to leaving the final
review, to make sure the state transitions all behaved.

## 11. Workflow Example

Here is what actually using the site looks like.

1. Sara wants a small extension built. She registers as a Client, picks
   a username and password, and lands on her client dashboard.
2. She clicks "Post a project", picks "Residential" as the category,
   writes the description, sets a budget range of 800,000 to 1,200,000,
   a location, and a deadline. She submits and the project shows as Open.
3. Bilal, a contractor, registers separately and uploads his company
   info. His account sits in Pending until an admin verifies him from
   the Django admin site.
4. Once verified, Bilal browses the open projects, filters by location,
   opens Sara's project, and submits a bid of 1,050,000 over 60 days.
5. Two more contractors bid as well. Sara opens her project page and
   sees all three bids on one screen, sorted by amount. She clicks
   "Award" on Bilal's bid. The project flips to In Progress and the
   other two bids are auto-rejected.
6. Bilal finishes the job a few weeks later and clicks "Mark completed"
   from his contractor dashboard. The project now says Completed but
   the review is not unlocked yet.
7. Sara visits the same page, sees the contractor's claim, and clicks
   "Confirm completion".
8. The review form opens. She picks 5 stars and writes a short comment.
   On save, Bilal's public profile updates with the new average rating,
   and his page shows the review under his other ones.

## 12. Results and Discussion

The platform does everything in the requirements section. The hardest
design call was the completion step. The first version had the
contractor mark the project complete and the review unlock right after,
but that gives the contractor too much control over their own rating
cycle. Splitting it into two clicks, contractor marks complete, then
client confirms, made the rating side fairer. The unique constraint on
bids saved me once in testing when a refreshed form would otherwise
have created a duplicate bid.

## 13. Limitations

There is no in-app messaging, so a client who has a question about a
bid has to call the contractor. There is no payment processing, no
notifications, and no file attachments on projects. Verification is a
manual click in the Django admin site. There is also no public API, so
a mobile client would need extra work.

## 14. Future Work

The natural next steps are a messaging feature between the client and
each bidder, file uploads for drawings and method statements, and email
notifications for the key state changes. After that, a REST API would
open the door to a mobile app, and a basic escrow flow would make the
platform useful for the money side of the job, not just the matching.

## 15. Conclusion

BuildBid is a small but complete bidding platform for construction
jobs. It runs the full path from posting to bidding to award to a
public rating, and it does it on a code base small enough to read in an
afternoon. There is plenty left to add, but the core loop works.

## 16. References

1. Django 6 docs, https://docs.djangoproject.com/en/6.0/
2. Django auth customisation,
   https://docs.djangoproject.com/en/6.0/topics/auth/customizing/
3. Tailwind CSS docs, https://tailwindcss.com/docs
4. Python 3 docs, https://docs.python.org/3/
5. MySQL 8.0 reference manual,
   https://dev.mysql.com/doc/refman/8.0/en/
