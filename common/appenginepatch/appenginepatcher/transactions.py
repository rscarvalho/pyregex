from google.appengine.api import apiproxy_stub_map
from google.appengine.ext import db
from django.dispatch import Signal 
from django.db.models import signals
from django.utils._threading_local import local
from functools import wraps

# Add signals which can be run after a transaction has been committed
signals.post_save_committed = Signal()
signals.post_delete_committed = Signal()

local = local()

# Patch transaction handlers, so we can support post_xxx_committed signals
run_in_transaction = db.run_in_transaction
if not hasattr(run_in_transaction, 'patched'):
    @wraps(run_in_transaction)
    def handle_signals(*args, **kwargs):
        try:
            if not getattr(local, 'in_transaction', False):
                local.in_transaction = True
                local.notify = []
            result = run_in_transaction(*args, **kwargs)
        except:
            local.in_transaction = False
            local.notify = []
            raise
        else:
            commit()
            return result
    handle_signals.patched = True
    db.run_in_transaction = handle_signals

run_in_transaction_custom_retries = db.run_in_transaction_custom_retries
if not hasattr(run_in_transaction_custom_retries, 'patched'):
    @wraps(run_in_transaction_custom_retries)
    def handle_signals(*args, **kwargs):
        try:
            result = run_in_transaction_custom_retries(*args, **kwargs)
        except:
            local.in_transaction = False
            local.notify = []
            raise
        else:
            commit()
            return result
    handle_signals.patched = True
    db.run_in_transaction_custom_retries = handle_signals

def hook(service, call, request, response):
    if call == 'Rollback':
        # This stores a list of tuples (action, sender, kwargs)
        # Possible actions: 'delete', 'save'
        local.in_transaction = True
        local.notify = []
apiproxy_stub_map.apiproxy.GetPostCallHooks().Append('tx_signals', hook)

def commit():
    local.in_transaction = False
    for action, sender, kwds in local.notify:
        signal = getattr(signals, 'post_%s_committed' % action)
        signal.send(sender=sender, **kwds)

def entity_saved(sender, **kwargs):
    if 'signal' in kwargs:
        del kwargs['signal']
    if getattr(local, 'in_transaction', False):
        local.notify.append(('save', sender, kwargs))
    else:
        signals.post_save_committed.send(sender=sender, **kwargs)
signals.post_save.connect(entity_saved)

def entity_deleted(sender, **kwargs):
    if 'signal' in kwargs:
        del kwargs['signal']
    if getattr(local, 'in_transaction', False):
        local.notify.append(('delete', sender, kwargs))
    else:
        signals.post_delete_committed.send(sender=sender, **kwargs)
signals.post_delete.connect(entity_deleted)
