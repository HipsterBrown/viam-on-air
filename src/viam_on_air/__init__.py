# SPDX-FileCopyrightText: 2023-present HipsterBrown <headhipster@hipsterbrown.com>
#
# SPDX-License-Identifier: Apache-2.0

import uvicorn

from .app import app


def run():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
