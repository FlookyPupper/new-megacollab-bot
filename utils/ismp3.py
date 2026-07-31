from config.groups import (BITRATES, SAMPLERATES)

async def ismp3(data: bytes, frames_required=3) -> bool:
    i = 0

    if data[:3] == b"ID3":
        if len(data) < 10:
            return False
        size = (
            ((data[6] & 0x7F) << 21) |
            ((data[7] & 0x7F) << 14) |
            ((data[8] & 0x7F) << 7)  |
            (data[9] & 0x7F)
        )
        if size > len(data):
            return False
        i = 10 + size

    frames = 0
    version = None
    samplerate = None

    while i + 4 <= len(data) and frames < frames_required:
        h = int.from_bytes(data[i:i+4], "big")

        # sync
        if (h >> 21) & 0x7FF != 0x7FF:
            return False

        ver = (h >> 19) & 0x3
        layer = (h >> 17) & 0x3
        bitrate_i = (h >> 12) & 0xF
        sr_i = (h >> 10) & 0x3
        pad = (h >> 9) & 0x1

        if ver not in (3, 2) or layer != 1:
            return False

        mpeg = 1 if ver == 3 else 2
        bitrate = BITRATES[(mpeg, 3)][bitrate_i]
        sr = SAMPLERATES[mpeg][sr_i]

        if bitrate is None or sr is None:
            return False

        if frames == 0:
            version, samplerate = mpeg, sr
        elif version != mpeg or samplerate != sr:
            return False

        if mpeg == 1:
            frame_len = int((144000 * bitrate) / sr + pad)
        else:
            frame_len = int((72000 * bitrate) / sr + pad)

        if frame_len <= 0 or i + frame_len > len(data):
            return False

        i += frame_len
        frames += 1

    return frames >= frames_required