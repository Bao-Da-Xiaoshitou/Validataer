#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理器 - 用于管理验证规则和关系规则
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from config import RULES_CONFIG, DEFAULT_RULES
