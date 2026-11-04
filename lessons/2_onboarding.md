---
title: "Live Demo: Getting Access"
teaching: 10
exercises: 0
questions:
  - How does a new user, and a new research group, get onto NRP?
  - What is a namespace, and who can administer one?
objectives:
  - Sign in through CILogon with campus credentials.
  - Request a namespace, and add members to one as its admin.
keypoints:
  - CILogon means you sign in with an existing campus account — no new password.
  - Compute lives in a **namespace**, which maps onto a research group or a course.
  - Namespace admins are faculty, staff, postdocs or PIs; they add everyone else as members.
---

**Time:** 00:15–00:25

This is the live part of the session: a new user signs in, and then becomes the
**admin of a namespace** in real time. Everything below is what you will see on
screen, and what you would do yourself afterwards.

## Who can use NRP

Users must be affiliated with a **U.S.-based project**, or be collaborating with
a U.S.-based researcher or educator. There is no separate NRP application for
that — access is granted through a namespace, below.

## Step 1 — Sign in with CILogon

NRP authenticates through **CILogon**, so you sign in with an existing campus
account — there is no NRP password to issue or reset.

Go to **[nrp.ai](https://nrp.ai/)** and sign in. CILogon asks **which identity
provider** to authenticate against, in this order of preference:

1. **Your own institution.** Search for it by name — your account is then tied to
   your campus identity and survives as long as your affiliation does.
2. **Google or Microsoft, using your campus email address.** If your institution
   is not listed, choose Google or Microsoft and pick your
   `@your-institution.edu` address, not a personal one.

Use the **same** provider every time: a different one produces a different NRP
identity, and namespace membership is attached to the identity, not to you.

Signing in creates your NRP identity. Nothing is allocated to you yet — but the
identity has to exist before anything can be.

## Step 2 — Namespaces: where a group lives

Compute on NRP lives in a **namespace** — a Kubernetes grouping that scopes
resources and membership. For a research group, the namespace *is* the group:

- **Admins** add and remove members and create resources. An admin must be
  **faculty, staff, a postdoc, or a PI** — not a student directly.
- **Users** work inside it. An admin adds students as regular members.
- Admins are also responsible for members following cluster policy.

![Namespaces, roles, and resource scope](images/namespaces.png)

Most of what you create — pods, deployments, services, secrets, storage claims —
is **namespace-scoped**: it lives in your group's namespace and is invisible to
everyone else's. That split is why a namespace is a safe sandbox.

## Step 3 — Request a namespace, or join one

Two routes, depending on where you stand:

**Starting a new group?** Submit the form at
**[get-started.nrp-nautilus.io](https://get-started.nrp-nautilus.io/)**. It asks
who you are, your institution, the email on your NRP account, and whether you
want the hosted LLM endpoints. An administrator reviews it, usually within a
working day, and replies by email.

**Joining an existing group?** Ask its admin to add you, and send them the
identity shown when you sign in at [nrp.ai](https://nrp.ai/).

> **Namespaces are requested by faculty, staff, and research scientists.** If
> you are a student, your advisor submits the request and adds you.

## What we do on screen

1. Sign in at nrp.ai with CILogon, as a brand-new user.
2. Show the identity NRP now holds for that user.
3. As the existing namespace admin, **add the new user to the namespace and make
   them an admin** — then confirm they can see it from their side.
4. Show the **namespaces view** to see the group appear.

- [NRP namespaces view](https://nrp.ai/viz/namespaces/)

## Where to get help afterwards

- **Documentation:** [NRP's Getting
  started](https://nrp.ai/documentation/userdocs/start/getting-started/) — the
  reference for installing `kubectl` and `kubelogin`, downloading your
  kubeconfig, and your first pod. We will not need it today.
- **Email NRP** — it goes to a ticketing system.
- **The NRP Slack workspace** — faster response; start at
  [nrp.ai/contact](https://nrp.ai/contact/).

::: callout Next
With access sorted, we put NRP's hosted LLMs to work from a notebook:
[AI-enabled research](3_ai.html).
:::
