#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
from typing import Any, Dict, List
import httpx
import os
from holehe.core import import_submodules, get_functions, launch_module
from holehe.modules import *

from classes.account.Account import Account
from classes.account.WebsiteAccount import WebsiteAccount
from classes.Profile import Profile
from classes.types.OpseStr import OpseStr
from tools.Tool import Tool

from utils.datatypes import DataTypeInput
from utils.datatypes import DataTypeOutput
from utils.stdout import print_debug, print_error, print_warning


class HoleheTool(Tool):
    """
    Class which describe a HoleheTool
    """
    """
    This code is inspired by: 
    https://github.com/megadose/holehe
    """
    deprecated = False

    # Import Modules
    modules = import_submodules("holehe.modules")
    websites = get_functions(modules)

    def __init__(self):
        """The constructor of a HoleheTool"""
        super().__init__()

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Function which return tool configuration as a dictionnary."""
        return {
            'active': True,
        }

    @staticmethod
    def get_lst_input_data_types() -> Dict[str, bool]:
        """
        Function which return the list of data types which can be use to run this Tool.
        It's will help to make decision to run Tool depending on current data.
        """
        return {
            DataTypeInput.EMAIL: True,
        }

    @staticmethod
    def get_lst_output_data_types() -> List[str]:
        """
        Function which return the list of data types which can be receive by using this Tool.
        It's will help to make decision to complete profile to get more information.
        """
        return [
            DataTypeOutput.ACCOUNT,
        ]

    def execute(self):

        emails: List[OpseStr] = self.get_default_profile().get_lst_emails()
        profile: Profile = self.get_default_profile().clone()

        for email in emails:
            print_debug("Investigating " + str(email) + " ...")
            try:
                accounts = self.list_website_accounts(email, profile)
                profile.set_lst_accounts(accounts)
            except Exception as e:
                print_error(" " + str(e), True)
                print_warning(" Profiles produced by HoleheTool might be incompleted due to an error")

        # Append completed profile
        self.append_profile(profile)

    def list_website_accounts(self, email, profile: Profile = None) -> List[Account]:
        """ """
        if profile == None:
            profile = Profile(lst_emails=[email], lst_accounts=[])

        results = []

        asyncio.run(self.holehetool_callback(email, results))

        accounts = []
        for result in results:
            try:
                if 'exists' in result.keys() and result.get('exists'):
                    # print_debug(email + " is register on " + result.get('name'))
                    account = WebsiteAccount(
                        login = email,
                        website_name = result.get('name'),
                        website_url = result.get('domain'),
                        recovery_email = result.get('emailrecovery'),
                        phone_number = result.get('phoneNumber')
                    )
                    accounts.append(account)
            except Exception as e:
                print_error(" [Holehe:holehe_call:" + result.get('name') + "] " + str(e), True)

        # Add found accounts to the profile
        return accounts


    async def holehe_module_callback(self, module, email: str, client, module_result) -> None:
        """ """
        try:
            await launch_module(module, email, client, module_result)
        except:
            print_warning(" " + str(module) + " has stopped during execution", True)


    async def holehetool_callback(self, email: str, module_result) -> None:
        """ """
        async with httpx.AsyncClient() as client:
            ret = await asyncio.gather(*[self.holehe_module_callback(module, email, client, module_result) for module in HoleheTool.websites])
        print_debug("Finalized all. Return is a list of len {} outputs.".format(len(ret)))
