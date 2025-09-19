import sys

# Patch: nếu thiếu audioop thì tạo dummy module
import types
if "audioop" not in sys.modules:
    sys.modules["audioop"] = types.ModuleType("audioop")

# Sau đó import discord như bình thường
import discord
