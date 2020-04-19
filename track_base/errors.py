#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Contains exception types that can be transported between server and client
"""

class RequestMalformed(Exception):
    """Something wrong about the request sent (see .error)"""
