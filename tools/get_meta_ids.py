"""One-time: turn a short Meta token into a page token that doesn't expire,
and find your Facebook Page id and Instagram account id.

    pip install requests
    python tools/get_meta_ids.py APP_ID APP_SECRET SHORT_USER_TOKEN

Get SHORT_USER_TOKEN from the Graph API Explorer (developers.facebook.com/tools/explorer):
pick your app, "Get User Access Token", and tick ALL of these permissions:
  pages_show_list, pages_read_engagement, pages_read_user_content, pages_manage_posts,
  pages_manage_engagement, publish_video, read_insights   (read_insights = Facebook views + watch time)
  instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_insights,
  business_management
"""
import sys

import requests

V = "v24.0"


def main(app_id: str, secret: str, short: str) -> None:
    r = requests.get(f"https://graph.facebook.com/{V}/oauth/access_token", params={
        "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": secret,
        "fb_exchange_token": short}, timeout=30)
    r.raise_for_status()
    long_user = r.json()["access_token"]
    need = {"read_insights", "instagram_manage_insights", "pages_read_engagement", "instagram_content_publish",
            "publish_video", "pages_manage_posts"}
    perms = requests.get(f"https://graph.facebook.com/{V}/me/permissions",
                         params={"access_token": long_user}, timeout=30).json().get("data", [])
    have = {x["permission"] for x in perms if x.get("status") == "granted"}
    if need - have:
        print("WARNING: this token is missing", ", ".join(sorted(need - have)),
              "- go back to the Graph API Explorer, tick them, and run this again.")
    pages = requests.get(f"https://graph.facebook.com/{V}/me/accounts", params={
        "fields": "id,name,access_token,instagram_business_account{id,username}",
        "access_token": long_user}, timeout=30).json()
    for p in pages.get("data", []):
        ig = p.get("instagram_business_account") or {}
        print(f"\nPage: {p['name']}")
        print("  FB_PAGE_ID      =", p["id"])
        print("  IG_USER_ID      =", ig.get("id", "(no Instagram linked to this page)"), ig.get("username", ""))
        print("  META_PAGE_TOKEN =", p["access_token"])
    if not pages.get("data"):
        print("No pages found. Check the token has pages_show_list and the page is yours.", pages)


if __name__ == "__main__":
    main(*sys.argv[1:4])
