import asyncio
import discord
from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import HCapsuleRequest

INVITE = input("Invite: ").strip()
CAPMONSTER_KEY = input("CapMonster API Key (press enter to skip): ").strip()

cm_lxc = (
    CapMonsterClient(options=ClientOptions(api_key=CAPMONSTER_KEY))
    if CAPMONSTER_KEY
    else None
)

async def solve_captcha_if_needed(e, token, invite_code):
    if not cm_lxc:
        print("[-] Error: Captcha triggered, but no CapMonster API key was provided.")
        return False

    try:
        response_data = getattr(e, "response", {}).get("json", {})
        sitekey = response_data.get("captcha_sitekey")
        rqdata = response_data.get("captcha_rqdata")

        if not sitekey:
            print("[-] Error: Could not extract hCaptcha sitekey from response.")
            return False

        print("[=] Solving Captcha via CapMonster...")

        capmonster_request = HCapsuleRequest(
            websiteUrl="https://discord.com",
            websiteKey=sitekey,
            metadata={"rqdata": rqdata} if rqdata else None,
        )

        solution = await cm_lxc.solve_captcha(capmonster_request)
        solved_token = solution.get("gRecaptchaResponse") or solution.get("token")

        if not solved_token:
            print("[-] Error: CapMonster failed to return a valid token.")
            return False

        print("[+] Successfully Joined solving captcha")
        return True

    except Exception as err:
        print(f"[-] Error during captcha handling: {err}")
        return False

async def run_client(token, invite_code):
    intents = discord.Intents.default()
    lxc = discord.Client(intents=intents, chunk_guilds_at_startup=False)

    @lxc.event
    async def on_ready():
        print(f"\n[Token Joiner in progress]")
        print(f"Client: {lxc.user}")

        try:
            await lxc.accept_invite(invite_code)
            print("[+] Joined Successfully")
        except discord.HTTPException as e:
            if e.status == 400 and (
                "captcha_key" in str(e.text).lower()
                or "captcha" in str(e.text).lower()
            ):
                print("[=] Captcha Required")
                await solve_captcha_if_needed(e, token, invite_code)
            else:
                print(f"[-] Error: Failed ({e.status}): {e.text}")
        except Exception as e:
            print(f"[-] Error: {type(e).__name__} - {e}")

        await lxc.close()

    try:
        await lxc.start(token)
    except Exception as e:
        print(f"\n[Token Joiner in progress]")
        print(f"[-] Error: Failed to login ({type(e).__name__})")

async def main():
    try:
        with open("tokens.txt", "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("[-] Error: 'tokens.txt' not found. Please create it in the same directory.")
        return

    if not tokens:
        print("[-] Error: 'tokens.txt' is empty.")
        return

    code = INVITE.rstrip("/").split("/")[-1]
    print(f"Loaded {len(tokens)} token(s) from tokens.txt")

    for index, token in enumerate(tokens, 1):
        await run_client(token, code)

        if index < len(tokens):
            await asyncio.sleep(2)

    print("\n[Token Joiner Finished]")
    print("All clients processed.")

asyncio.run(main())
