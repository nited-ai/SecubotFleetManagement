# Monkey-patch aioice.Connection to use a fixed username and password accross all instances.

import aioice


class Connection(aioice.Connection):
    local_username = aioice.utils.random_string(4)
    local_password = aioice.utils.random_string(22)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_username = Connection.local_username
        self.local_password = Connection.local_password


aioice.Connection = Connection  # type: ignore


# Monkey-patch aiortc.rtcdtlstransport.X509_DIGEST_ALGORITHMS to remove extra SHA algorithms
# Extra SHA algorithms introduced in aiortc 1.10.0 causes Unity Go2 to use the new SCTP format, despite aiortc using the old SCTP syntax.
# This new format is not supported by aiortc version as of today (2025-06-02)


import aiortc
import logging
from packaging.version import Version


# ============================================================================
# CRITICAL WORKAROUND: aiortc Race Condition Fix
# ============================================================================
# DO NOT REMOVE THIS MONKEY-PATCH WITHOUT TESTING!
#
# This monkey-patch fixes a critical race condition in aiortc that causes
# Remote WebRTC connections to fail with:
#   AttributeError: 'NoneType' object has no attribute 'media'
#
# Root cause: setRemoteDescription() triggers __connect() task before
# internal state is fully initialized, causing __remoteRtp() to access
# None values.
#
# This is part 1 of a 2-part fix. Part 2 is in webrtc_driver.py.
#
# For full documentation, see: .agent-os/product/aiortc-race-condition-fix.md
#
# Affected versions: aiortc 1.9.0, 1.10.0, 1.11.0+
# Date added: 2026-02-04
# ============================================================================

from aiortc import RTCPeerConnection

_original_remoteRtp = RTCPeerConnection._RTCPeerConnection__remoteRtp  # type: ignore


def __remoteRtp_with_null_check(self, transceiver):
    """
    Patched version of __remoteRtp that adds null checking for __remoteDescription().
    This prevents the race condition where __connect() task tries to access
    __remoteDescription().media before the remote description is fully set.
    """
    try:
        # Check if remote description is set before accessing it
        remote_desc = self._RTCPeerConnection__remoteDescription()  # type: ignore
        if remote_desc is None:
            logging.debug(f"__remoteRtp called but remote description is None, skipping for now")
            return

        # Call the original method
        return _original_remoteRtp(self, transceiver)

    except AttributeError as e:
        # If we still get an AttributeError, log it but don't crash
        logging.debug(f"Race condition in __remoteRtp: {e}")
        return


# Apply the monkey patch
RTCPeerConnection._RTCPeerConnection__remoteRtp = __remoteRtp_with_null_check  # type: ignore


if Version(aiortc.__version__) == Version("1.10.0"):
    X509_DIGEST_ALGORITHMS = {
        "sha-256": "SHA256",
    }
    aiortc.rtcdtlstransport.X509_DIGEST_ALGORITHMS = X509_DIGEST_ALGORITHMS

elif Version(aiortc.__version__) >= Version("1.11.0"):
    # Syntax changed in aiortc 1.11.0, so we need to use the hashes module
    from cryptography.hazmat.primitives import hashes

    X509_DIGEST_ALGORITHMS = {
        "sha-256": hashes.SHA256(),  # type: ignore
    }
    aiortc.rtcdtlstransport.X509_DIGEST_ALGORITHMS = X509_DIGEST_ALGORITHMS