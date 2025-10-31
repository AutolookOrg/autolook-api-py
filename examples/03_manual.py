"""
An example of buying a new email and manually unlocking the first mails it received
"""

from autolook_api import AlApiClient, Error, l
from autolook_api import alapi
import asyncio
import dotenv
import os
import time

async def main():
    dotenv.load_dotenv()

    alacctoken = os.getenv("ALACCTOKEN")

    alcli = AlApiClient(alacctoken, debug=True)
    
    try:
        await alcli.start()

        balance = await alcli.get_balance()
        print(f"Balance:", balance)
        if balance <= 0:
            l().error("Balance is zero, can't continue!")
            return
        
        api_info = await alcli.get_api_info()
        print(f"Stock domains:", api_info.stock_domains)
        
        email = await alcli.buy_email("outlook.com")
        
        l().info(f"Waiting till email: '{email}' receives a new mail")
        
        time_start = time.perf_counter()
        new_mails = await alcli.get_new_mails_loop(email, timeout_secs=600)
        l().info(f"New mails after: {time.perf_counter() - time_start} seconds, found mails: {len(new_mails)}")
        for mail in new_mails:
            l().debug("- Mail NEW: %s", mail.__str__())

        time_start_unlocking = time.perf_counter()
        locked_mails = [mail for mail in new_mails if not mail.unlocked]
        if len(locked_mails) > 0:
            l().debug(f"Unlocking mails: {len(locked_mails)}")
            unlocked_mails = await alcli.unlock_mails(email, [mail.almailid for mail in locked_mails], True)
            l().info(f"Unlocked mails: {time.perf_counter() - time_start_unlocking} seconds, unlocked mails: {len(unlocked_mails)}")
            for mail in unlocked_mails:
                l().debug("- Mail UNLOCKED: %s", mail.__str__())

        print("---\nDone")
        
    except Error as e:
        l().error(f"{e}", exc_info=True)
    except Exception as e:
        l().error(f"Unexpected: {e}", exc_info=True)
    except KeyboardInterrupt as e:
        l().info("User signaled shutdown, exiting...")
    finally:
        await alcli.close()


if __name__ == "__main__":
    asyncio.run(main())
