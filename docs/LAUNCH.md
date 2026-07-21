# Local Time Tracker Launch Kit

This document contains the English positioning, repository metadata, launch
copy, and rollout checklist for Local Time Tracker.

## Positioning

### One-line promise

> See where your Windows time goes — without sending your activity anywhere.

### Repository description

> A private, automatic Windows time tracker for applications and browser tabs. Local storage, no account, no telemetry.

### Suggested GitHub topics

`windows`, `time-tracker`, `productivity`, `privacy`, `offline-first`,
`desktop-app`, `python`, `sqlite`, `activity-tracker`, `open-source`

### Primary audiences

- privacy-conscious Windows users;
- developers and independent professionals who want automatic activity insight;
- students who want to understand computer usage without a subscription;
- open-source users looking for a focused, easy-to-install Windows tool.

### Message hierarchy

1. Activity never needs to leave the computer.
2. Tracking is automatic; no manual timer is required.
3. The app shows applications, browser tabs, idle time, and useful summaries.
4. Installation is straightforward and the project is open source.

## Repository launch checklist

- [x] Put the benefit and download link at the top of the README.
- [x] Add a representative product visual.
- [x] Add contribution, support, security, conduct, and roadmap files.
- [x] Add structured bug and feature request forms.
- [x] Seed three contributor-friendly issues for documentation, tests, and
      sanitized screenshots.
- [x] Prepare a 1280 × 640 social preview under `assets/`.
- [ ] Upload `assets/social-preview.png` under **Settings → General → Social preview**.
- [x] Add the repository description and topics listed above.
- [x] Enable GitHub Discussions and private vulnerability reporting.
- [x] Create welcome, feature-request, and beta-testing discussions:
      [welcome](https://github.com/HafidIdrissi/Time-Tracker/discussions/1),
      [beta testing](https://github.com/HafidIdrissi/Time-Tracker/discussions/2),
      and [privacy controls](https://github.com/HafidIdrissi/Time-Tracker/discussions/3).
- [ ] Add sanitized desktop screenshots from a demonstration database.
- [ ] Sign the installer or publish a clear checksum and scan disclosure.

## Posting principles

- Ask for testers and honest feedback before asking for stars.
- Use a sanitized screenshot or short product demonstration with every post.
- Adapt each post to the community and read its current self-promotion rules.
- Do not post the same message to multiple communities on the same day.
- Answer every substantive comment, including critical feedback.
- Never buy stars, votes, reviews, or artificial engagement.

## Hacker News

### Suggested title

> Show HN: Local Time Tracker – private, automatic activity tracking for Windows

### Suggested post

> I built Local Time Tracker because I wanted a simple way to understand where my Windows time was going without sending window titles or browsing activity to a cloud service.
>
> It automatically tracks the foreground application, window title, browser tab, and idle periods. The dashboard shows today and the last seven days, and it can generate standalone HTML reports that work offline.
>
> Everything is stored in a local SQLite database. There is no account, advertising, telemetry, or required server. The project is MIT licensed and includes a Windows installer.
>
> I would especially value feedback on the first-run experience, the usefulness of the analysis, and privacy controls that should be prioritized next.
>
> Source and Windows download: https://github.com/HafidIdrissi/Time-Tracker

## Reddit and community forums

### Suggested title

> I built a private, open-source Windows time tracker with no account or cloud

### Suggested post

> I have released Local Time Tracker, a free Windows application that automatically measures time spent in applications and browser tabs.
>
> The main design constraint is privacy: activity stays in a local SQLite database. The app has no account, cloud synchronization, advertising, or telemetry. It includes idle detection, daily and seven-day analysis, application and tab rankings, and offline HTML reports.
>
> I am looking for Windows users willing to test the installer and give honest feedback, particularly about setup, accuracy, and missing privacy controls. Please do not share screenshots containing real window titles.
>
> Project and download: https://github.com/HafidIdrissi/Time-Tracker

Potential communities include open-source, Windows, productivity, quantified
self, and privacy communities. Check each community's current rules before
posting.

## Product Hunt

### Product name

Local Time Tracker

### Tagline

> Private, automatic time tracking for Windows

### Short description

> Understand time spent in Windows applications and browser tabs with local storage, offline reports, and no account or telemetry.

### First comment

> I built Local Time Tracker for people who want automatic activity insights without giving a cloud service access to their window titles or browsing context.
>
> The application records the foreground Windows application, title, browser tab, and idle state, then turns that data into daily and seven-day summaries. Everything remains in a local SQLite database and generated reports work completely offline.
>
> This is an early open-source release, so feedback on onboarding, accuracy, and the next privacy controls would be extremely useful.

## LinkedIn

> I have released Local Time Tracker, a free and open-source Windows application for understanding how time is spent across applications and browser tabs.
>
> The product is built around a simple privacy promise: activity stays on the user's computer. There is no account, cloud service, advertising, or telemetry. Local Time Tracker includes automatic foreground-window tracking, idle detection, seven-day analysis, and offline HTML reports.
>
> I am now looking for Windows users who can test the first release and share candid feedback about installation, clarity, and useful next features.
>
> https://github.com/HafidIdrissi/Time-Tracker

## X and Mastodon

### Short version

> I built Local Time Tracker: a free, open-source Windows app that automatically tracks time in applications and browser tabs. Local SQLite storage, offline reports, no account, no cloud, no telemetry. Feedback welcome: https://github.com/HafidIdrissi/Time-Tracker

### Thread opener

> Window titles can reveal a lot about a person's work. I wanted useful activity insights without sending that context to someone else's server, so I built Local Time Tracker for Windows. 🧵

Follow with one post about automatic tracking, one about local storage and
privacy, one sanitized screenshot, and the repository link.

## Direct outreach

### Subject

> Open-source Windows time tracker for your privacy/productivity audience

### Email

> Hello,
>
> I recently released Local Time Tracker, a free and open-source Windows application that automatically measures time spent in applications and browser tabs while keeping all activity in a local SQLite database.
>
> It requires no account and includes no advertising or telemetry. Users can view daily and seven-day analysis and generate standalone offline reports.
>
> I thought it might be relevant to your audience because of its local-first privacy approach. The source code and Windows installer are available here:
>
> https://github.com/HafidIdrissi/Time-Tracker
>
> I would be happy to provide sanitized screenshots, technical details, or answer questions. There is no expectation of coverage.
>
> Best regards,
> IDRISSI HAFID — H.I. SOLUTIONS

## Four-week rollout

### Week 1: proof and polish

- recruit 10–20 Windows testers from personal and professional contacts;
- record installation problems and repeated questions;
- publish sanitized screenshots and improve first-run documentation;
- resolve the highest-impact defects before broad promotion.

### Week 2: focused communities

- publish in one relevant community at a time;
- collect feedback in Discussions and issues;
- share a short progress update after implementing user feedback.

### Week 3: launch platforms

- publish the Show HN and Product Hunt launches when the installer is stable;
- contact a small number of relevant newsletters or independent reviewers;
- list the project on appropriate open-source and Windows software directories.

### Week 4: visible follow-through

- publish a new release based on real feedback;
- write a short changelog post thanking testers and contributors;
- share concrete improvements rather than repeating the original announcement.

## Metrics to review weekly

- unique repository visitors and clones;
- release asset downloads;
- installer or startup problems reported;
- discussions and actionable issues;
- returning contributors;
- stars earned after each launch activity.

Stars are a useful signal, but successful promotion should first produce genuine
users, feedback, downloads, and repeat participation.
