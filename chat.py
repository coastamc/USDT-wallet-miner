import asyncio
import aiofiles
import logging
from mnemonic import Mnemonic
from web3 import Web3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Constants
BNB_RPC_URL = "https://bsc-dataseed.binance.org/"
USDT_CONTRACT_ADDRESS = Web3.to_checksum_address("0x55d398326f99059ff775485246999027b3197955")
LOG_FILE = "wallets_log.txt"
BALANCE_LOG_FILE = "wallets_with_balance.txt"
NUM_ACCOUNTS = 10

# Initialize Mnemonic and Web3
mnemo = Mnemonic("english")
web3 = Web3(Web3.HTTPProvider(BNB_RPC_URL))

# Enable HD wallet features
web3.eth.account.enable_unaudited_hdwallet_features()

def generate_bnb_account():
    """Generate a new Binance Smart Chain account using a mnemonic phrase."""
    mnemonic = mnemo.generate(128)
    bnb_account = web3.eth.account.from_mnemonic(mnemonic)
    return mnemonic, bnb_account.address

async def get_usdt_balance(address):
    """Check the USDT balance of a given Binance Smart Chain address."""
    checksummed_address = Web3.to_checksum_address(address)
    contract = web3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=[{
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }])
    
    try:
        balance = contract.functions.balanceOf(checksummed_address).call()
        return balance / 1e6  # Convert from wei to USDT (USDT has 6 decimal places)
    except Exception as e:
        logger.error(f"Error fetching USDT balance for {address}: {e}")
        return 0

async def process_account(c):
    try:
        usdt_mnemonic, usdt_address = generate_bnb_account()
        usdt_balance = await get_usdt_balance(usdt_address)

        # Print the mnemonic phrase
        print(f"Round {c}: Mnemonic: {usdt_mnemonic}")

        # Check if the balance is greater than 0
        if usdt_balance > 0:
            logger.info(f"Round {c}: USDT Address: {usdt_address}, Balance: {usdt_balance:.6f} USDT, Mnemonic: {usdt_mnemonic}")

            # Write to a separate file for wallets with a balance
            async with aiofiles.open(BALANCE_LOG_FILE, "a", encoding="utf-8") as log_file:
                await log_file.write(
                    f"USDT: Mnemonic: {usdt_mnemonic}, Address: {usdt_address}, Balance: {usdt_balance:.6f} USDT\n\n"
                )
        else:
            logger.info(f"Round {c}: USDT Address: {usdt_address}, Balance: {usdt_balance:.6f} USDT (not saved)")

    except Exception as e:
        logger.error(f"Error in processing account: {e}")

async def main():
    count = 1
    try:
        while True:
            tasks = [process_account(count + i) for i in range(NUM_ACCOUNTS)]
            await asyncio.gather(*tasks)
            count += NUM_ACCOUNTS
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")

if __name__ == "__main__":
    asyncio.run(main())
