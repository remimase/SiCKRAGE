# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
from urlparse import urljoin

import sickrage
from sickrage.core.websession import WebSession


class SabNZBd(object):
    @staticmethod
    def sendNZB(nzb):
        """
        Sends an NZB to SABnzbd via the API.
        :param nzb: The NZBSearchResult object to send to SAB
        """

        category = sickrage.app.config.sab_category
        if nzb.show.is_anime:
            category = sickrage.app.config.sab_category_anime

        # if it aired more than 7 days ago, override with the backlog category IDs
        for curEp in nzb.episodes:
            if datetime.date.today() - curEp.airdate > datetime.timedelta(days=7):
                category = sickrage.app.config.sab_category_anime_backlog if nzb.show.is_anime else sickrage.app.config.sab_category_backlog

        # set up a dict with the URL params in it
        params = {'output': 'json'}
        if sickrage.app.config.sab_username:
            params['ma_username'] = sickrage.app.config.sab_username
        if sickrage.app.config.sab_password:
            params['ma_password'] = sickrage.app.config.sab_password
        if sickrage.app.config.sab_apikey:
            params['apikey'] = sickrage.app.config.sab_apikey

        if category:
            params['cat'] = category

        if nzb.priority:
            params['priority'] = 2 if sickrage.app.config.sab_forced else 1

        sickrage.app.log.info('Sending NZB to SABnzbd')
        url = urljoin(sickrage.app.config.sab_host, 'api')

        try:
            jdata = None

            if nzb.resultType == 'nzb':
                params['mode'] = 'addurl'
                params['name'] = nzb.url
                jdata = WebSession().get(url, params=params, verify=False).json()
            elif nzb.resultType == 'nzbdata':
                params['mode'] = 'addfile'
                multiPartParams = {'nzbfile': (nzb.name + '.nzb', nzb.extraInfo[0])}
                jdata = WebSession().get(url, params=params, file=multiPartParams, verify=False).json()

            if not jdata:
                raise Exception
        except Exception:
            sickrage.app.log.info('Error connecting to sab, no data returned')
            return False

        sickrage.app.log.debug('Result text from SAB: {}'.format(jdata))

        result, error_ = SabNZBd._checkSabResponse(jdata)
        return result

    @staticmethod
    def _checkSabResponse(jdata):
        """
        Check response from SAB
        :param jdata: Response from requests api call
        :return: a list of (Boolean, string) which is True if SAB is not reporting an error
        """
        error = jdata.get('error')

        if error:
            sickrage.app.log.error(error)
            return False, error
        else:
            return True, jdata

    @staticmethod
    def getSabAccesMethod(host=None):
        """
        Find out how we should connect to SAB
        :param host: hostname where SAB lives
        :param username: username to use
        :param password: password to use
        :param apikey: apikey to use
        :return: (boolean, string) with True if method was successful
        """
        params = {'mode': 'auth', 'output': 'json'}
        url = urljoin(host, 'api')
        data = WebSession().get(url, params=params, verify=False).json()
        if not data:
            return False, data

        return SabNZBd._checkSabResponse(data)

    @staticmethod
    def test_authentication(host=None, username=None, password=None, apikey=None):
        """
        Sends a simple API request to SAB to determine if the given connection information is connect
        :param host: The host where SAB is running (incl port)
        :param username: The username to use for the HTTP request
        :param password: The password to use for the HTTP request
        :param apikey: The API key to provide to SAB
        :return: A tuple containing the success boolean and a message
        """

        # build up the URL parameters
        params = {
            'mode': 'queue',
            'output': 'json',
            'ma_username': username,
            'ma_password': password,
            'apikey': apikey
        }

        url = urljoin(host, 'api')

        data = WebSession().get(url, params=params, verify=False).json()
        if not data:
            return False, data

        # check the result and determine if it's good or not
        result, sabText = SabNZBd._checkSabResponse(data)
        if not result:
            return False, sabText

        return True, 'Success'
