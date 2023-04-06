# -*- coding: utf-8 -*-

'''
Módulo Bot System.
'''

from __future__ import annotations
from typing import TYPE_CHECKING

import json

from abc import abstractmethod
from os.path import exists
from time import time_ns
from random import choice, seed
from datetime import datetime

import discord

from discord.ext import commands, tasks
from discord.ext.commands import HelpCommand

if TYPE_CHECKING:
    from source.guild import Guild


class Bot(commands.Bot):

    '''
    Bot customizado.
    '''

    # Atributos privados
    _name: str
    _version: str
    _token: str
    _admins_id: list
    _users: dict
    _custom_guilds: dict
    _activity_str: str
    _custom_ready: bool

    def __init__(self,
                 command_prefix: str,
                 help_command: HelpCommand,
                 name: str,
                 settings_file: str,
                 intents,
                 version: str) -> None:

        super().__init__(command_prefix=command_prefix, help_command=help_command, intents=intents)

        self._name = name
        self._version = version
        self._custom_guilds = {}
        self._users = {}
        self._admins_id = []
        self._token = ""
        self._activity_str = ""
        self._custom_ready = False

        self.log('Bot', f'Initializing {self._name} {self._version}')
        self.log('Bot', 'Initializing the RNG')

        seed(time_ns())
        self.set_internal_settings(settings_file)

    # Getters e Setters
    @property
    def custom_guilds(self) -> dict:
        '''
        Getter dos servers.
        '''

        return self._custom_guilds

    # Loops
    @tasks.loop(seconds=600.0)  # 10 minutos
    async def save(self) -> None:
        '''
        Salva os dados.
        '''

        self.log('Bot', 'Saving all guilds automatically')
        self.save_all_guilds()

    # Eventos
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        '''
        Evento de "dados preparados".
        '''

        self.log('Bot', 'Ready')
        await self.prepare_data()

    @commands.Cog.listener()
    async def on_connect(self) -> None:
        '''
        Evento de conexão.
        '''

        self.log('Bot', 'Connected')

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        '''
        Evento de desconexão.
        '''

        self.log('Bot', 'Disconnected')

    @commands.Cog.listener()
    async def on_resumed(self) -> None:
        '''
        Evento de retorno.
        '''

        self.log('Bot', 'Resumed')

    # Métodos
    @abstractmethod
    async def setup_hook(self) -> None:
        '''
        Pré-setup.
        '''

    @abstractmethod
    def load_guilds(self) -> None:
        '''
        Carrega os servidores.
        '''

    async def prepare_data(self) -> None:
        '''
        Prepara os dados e a presença.
        '''

        if not self._custom_ready:
            self._custom_ready = True
        else:
            return

        self.log('Bot', 'Waiting...')
        await self.wait_until_ready()

        self.load_guilds()

        if self.user is not None:
            self.log('Bot', f'{self._name} {self._version} ready to operate')
            self.log('Bot', f'Logged as {self.user.name}, with the id: {self.user.id}')

            await self.set_activity()
        else:
            self.log('Bot', 'Failed to get the user data')
            await self.set_activity('ERROR')

    async def set_activity(self, activity: str = '') -> None:
        '''
        Define a atividade.
        '''

        if activity != '':
            await self.change_presence(activity=discord.Game(name=activity))
        else:
            await self.change_presence(activity=discord.Game(name=self._activity_str))

    # Métodos
    def load_internal_settings(self, path: str) -> dict | None:
        '''
        Carrega as configurações internas.
        '''

        if path == "":
            return None

        if exists(path):
            with open(path, 'r+', encoding='utf-8') as internal_settings_file:
                internal_settings_json = internal_settings_file.read()

            return json.loads(internal_settings_json)

        self.log('Bot',
                 'The loading operation has failed. The file '
                 '"internal_settings.json" should be in the system directory')

        return None

    def set_internal_settings(self, path: str) -> None:
        '''
        Define as configurações internas.
        '''

        self.log('Bot', 'Loading internal definitions')

        internal_settings = self.load_internal_settings(path)

        if internal_settings is not None:
            self._admins_id = list(map(int, internal_settings['ADM_ID']))
            self._token = internal_settings['TOKEN']
            self._activity_str = choice(internal_settings['Activities'])
        else:
            self.log('Bot', 'Failed set internal definitions')

    def run(self, *args: tuple, **kwargs: tuple) -> None:
        '''
        Roda o bot.
        '''

        args += (self._token,)  # type: ignore

        return super().run(*args, **kwargs)  # type: ignore

    def save_guild(self, guild_id: int) -> None:
        '''
        Salva as configurações e dados do servidor específico.
        '''

        self._custom_guilds[str(guild_id)].write_settings()
        self._custom_guilds[str(guild_id)].write_data()

    def save_all_guilds(self) -> None:
        '''
        Salva as configurações de todos os servidores.
        '''

        for guild in self._custom_guilds.values():
            guild.write_settings()
            guild.write_data()

    def is_admin(self, author_id: int) -> bool:
        '''
        Checa se o autor é um administrador.
        '''

        return author_id in self._admins_id

    def get_info(self) -> dict:
        '''
        Retorna um dicionário com informações.
        '''

        info = {'Name': self._name,
                'Version': self._version,
                'HTTP loop': self.http,
                'Latency': self.latency,
                'Guild count': len(self.guilds),
                'Voice clients': self.voice_clients}

        return info

    def get_custom_guild(self, guild_id: int) -> Guild:
        '''
        Retorna um server personalizado.
        '''

        return self._custom_guilds[str(guild_id)]

    def log(self, origin: str, message: str) -> None:
        '''
        Exibe uma mensagem no console.
        '''

        print(f"[{datetime.now()}][{origin}]: {message}")
