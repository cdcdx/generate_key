import inquirer
import argparse
import os
import platform
import sys
import time
from eth_account import Account
from web3 import Web3
from loguru import logger
from questionary import Choice, select
from termcolor import cprint


# Contract ABI
contract_abi_usdc = [
    {
        "inputs": [
            { "internalType": "address", "name": "account", "type": "address" }
        ],
        "name": "balanceOf",
        "outputs": [
            { "internalType": "uint256", "name": "", "type": "uint256" }
        ], 
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "address", "name": "owner", "type": "address" },
            { "internalType": "address", "name": "spender", "type": "address" }
        ],
        "name": "allowance",
        "outputs": [
            { "internalType": "uint256", "name": "", "type": "uint256" }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "address", "name": "spender", "type": "address" }, 
            { "internalType": "uint256", "name": "amount", "type": "uint256" }
        ],
        "name": "approve",
        "outputs": [
            { "internalType": "bool", "name": "", "type": "bool" }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
]

def get_address_by_key(key):
    account = Account.from_key(key)
    return account.address

def get_file_content(file_name):
    with open(file_name, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    return data

def get_data_for_key(name):
    if name == '':
        file = f'generate/wallets.txt'
    else:
        file = f'generate/wallets-{name}.txt'
    datas = get_file_content(file)
    return datas

def set_data_for_key(name, privatekey, address):
    if name == '':
        file = f'generate/wallets.txt'
    else:
        file = f'generate/wallets-{name}.txt'
    file_data = ""
    with open(file, "r") as f:
        for line in f:
            line = line.replace(privatekey, f"{privatekey},{address}")
            file_data += line
    with open(file, "w") as f:
        f.write(file_data)

def set_data_add_key(name, privatekey):
    if not os.path.exists('generate'):
        os.makedirs('generate')
    
    if name == '':
        file = f'generate/wallets.txt'
    else:
        file = f'generate/wallets-{name}.txt'
    with open(file, "a") as f:
        f.writelines(privatekey + '\n')

def generate_privkey(name):
    while True:
        try:
            enter_count = [
                inquirer.Text('count', message="👉 输入账户数量")
            ]
            count = int(inquirer.prompt(enter_count, raise_keyboard_interrupt=True)['count'])
            if count > 0:
                break
            else:
                logger.info("❌  请输入正数.\n")
        except ValueError:
            logger.info("❌  请输入一个数字.\n")
    for id in range(count):
        acct = Account.create()
        privatekey = acct.key.hex()
        set_data_add_key(name, privatekey)
        logger.info(f"id: {id} privatekey: {privatekey}")
    logger.success(f"批量生成 {count} 钱包私钥 -> generate/wallets-{name}.txt")

def generate_address(name):
    datas = get_data_for_key(name)
    count = len(datas)
    while True:
        if not datas:
            logger.debug(f"nokey")
            break
        else:
            data = datas.pop(0)
            id = count-len(datas)
        logger.debug(f"id: {id} data: {data}")
        if len(data.split(',')) == 2:
            continue
        privatekey=data.split(',')[0]
        address = get_address_by_key(privatekey)
        set_data_for_key(name, privatekey, address)
        logger.info(f"id: {id} address: {address}")
    logger.success(f"批量计算 {count} 钱包地址 -> generate/wallets-{name}.txt")

def generate_balance(name):
    datas = get_data_for_key(name)
    count = len(datas)
    while True:
        if not datas:
            logger.debug(f"nokey")
            break
        else:
            data = datas.pop(0)
            id = count-len(datas)
        logger.debug(f"id: {id} data: {data}")
        privatekey=data.split(',')[0]
        address = get_address_by_key(privatekey)

        web3_obj = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        # 连接rpc节点
        connected = web3_obj.is_connected()
        if not connected:
            logger.error(f"Ooops! Failed to eth.is_connected.")
            raise Exception("Failed to eth.is_connected.")
        
        # 钱包地址
        sender_address = web3_obj.eth.account.from_key(privatekey).address
        sender_balance_eth = web3_obj.eth.get_balance(sender_address)
        balance_eth = web3_obj.from_wei(sender_balance_eth, 'ether')
        logger.debug(f"sender_balance_eth: {balance_eth} ETH")
        # USDC合约地址
        usdc_address = Web3.to_checksum_address('0x833589fcd6edb6e08f4c7c32d4f71b54bda02913')
        usdc_contract = web3_obj.eth.contract(address=usdc_address, abi=contract_abi_usdc)
        # 账户余额
        sender_balance_usdc = usdc_contract.functions.balanceOf(sender_address).call()
        balance_usdc = web3_obj.from_wei(sender_balance_usdc, 'mwei')
        logger.debug(f"sender_balance_usdc: {balance_usdc} USDC")
        
        logger.info(f"id: {id} address: {address} balance: {balance_eth} ETH / {balance_usdc} USDC")
        
        time.sleep(1)
    logger.success(f"批量查询 {count} 钱包地址 -> generate/wallets-{name}.txt")
    
def choose_name() -> str:
    enter_name = [
        inquirer.Text('name', message="👉 输入名字")
    ]
    name = inquirer.prompt(enter_name, raise_keyboard_interrupt=True)['name']
    return name

def main():
    # 初始化参数
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', type=bool, default=False, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    run_debug = bool(args.debug)
    
    # 日志级别
    log_level = "DEBUG" if run_debug else "INFO"
    logger.remove()
    logger.add(sys.stdout, level=log_level)

    try:
        while True:
            if platform.system().lower() == 'windows':
                os.system("title main")
            answer = select(
                '选择',
                choices=[
                    Choice("🔥 批量生成ETH私钥",  'generate_privkey', shortcut_key="1"),
                    Choice("🚀 批量计算ETH地址",  'generate_address', shortcut_key="2"),
                    Choice("🚀 批量查询USDC余额", 'generate_balance', shortcut_key="3"),
                    Choice('❌ Exit', "exit", shortcut_key="0")
                ],
                use_shortcuts=True,
                use_arrow_keys=True,
            ).ask()
            if answer == 'generate_privkey':
                name = choose_name()
                generate_privkey(name)
            elif answer == 'generate_address':
                name = choose_name()
                generate_address(name)
            elif answer == 'generate_balance':
                name = choose_name()
                generate_balance(name)
            elif answer == 'exit':
                sys.exit()
    except KeyboardInterrupt:
        cprint(f'\n 退出，请按<Ctrl + C>', color='light_yellow')
        sys.exit()


if __name__ == '__main__':
    main()
