# GitHub wiki content

[Home.md](Home.md) is the ready-to-publish wiki landing page.
[_Sidebar.md](_Sidebar.md) provides optional navigation.

The wiki is a separate Git repository. Adding these files to the application repository does **not** publish them to the GitHub Wiki tab.

## Publish the first page

1. While signed in as a maintainer, open [the repository wiki](https://github.com/HafidIdrissi/Time-Tracker/wiki) and choose **Create the first page** or **New Page**.
2. Use the title **Home** and Markdown format.
3. Open [Home.md](Home.md), choose **Raw**, and copy its complete content into the wiki editor.
4. Enter a short edit message and select **Save Page**.
5. Open the published page and check its links. To add navigation, use **Add a custom sidebar**, copy [_Sidebar.md](_Sidebar.md), and save it.

If Home or a sidebar already exists when publishing, review it before editing and preserve unrelated content.

GitHub documents these steps in [Adding or editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).

## Maintain the content

Keep the detailed guides in their existing repository files; the wiki summarizes them and links to the current guides. When a linked guide changes, check whether its wiki summary needs updating. Copy reviewed changes to the separate wiki after updating these source files.

Do not advertise the wiki in the root README until the live Home page is published and verified. Use fictional activity for demonstrations. Never include a personal database, report, private title or credential.

## Validation

For changes to these Markdown files:

- Preview Home and the sidebar in GitHub, check table/code formatting, and follow their links.
- Check that repository file links still exist and that README section anchors match the headings.
- Confirm the install/data-mode descriptions against the current README and privacy policy.
- After publication, verify the actual wiki and sidebar render correctly.

Application test suites are not required for a documentation-only wiki change. Record checks actually performed and keep source inspection separate from a real Windows walkthrough.
