from .zaplecze_all import *
from .zaplecze_detail import *
from .zaplecze_structure import *
from .zaplecze_create import *
from .zaplecze_write import *
from .zaplecze_classic import *
from .zaplecze_comp import *
from .zaplecze_ceneo import *
from .zaplecze_vis import *
from .panel_primislao import *
from .front import *

from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    return redirect('/')
