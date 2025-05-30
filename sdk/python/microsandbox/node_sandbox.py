"""
Node.js-specific sandbox implementation for the Microsandbox Python SDK.
"""

import uuid

import aiohttp

from .base_sandbox import BaseSandbox
from .execution import Execution


class NodeSandbox(BaseSandbox):
    """
    Node.js-specific sandbox for executing JavaScript code.
    """

    async def get_default_image(self) -> str:
        """
        Get the default Docker image for Node.js sandbox.

        Returns:
            A string containing the Docker image name and tag
        """
        return "microsandbox/node"

    async def run(self, code: str) -> Execution:
        """
        Execute JavaScript code in the sandbox.

        Args:
            code: JavaScript code to execute

        Returns:
            An Execution object that represents the executed code

        Raises:
            RuntimeError: If the sandbox is not started or execution fails
        """
        if not self._is_started:
            raise RuntimeError("Sandbox is not started. Call start() first.")

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        request_data = {
            "jsonrpc": "2.0",
            "method": "sandbox.repl.run",
            "params": {
                "sandbox": self._name,
                "namespace": self._namespace,
                "language": "nodejs",
                "code": code,
            },
            "id": str(uuid.uuid4()),
        }

        try:
            async with self._session.post(
                f"{self._server_url}/api/v1/rpc",
                json=request_data,
                headers=headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to execute code: {error_text}")

                response_data = await response.json()
                if "error" in response_data:
                    raise RuntimeError(
                        f"Failed to execute code: {response_data['error']['message']}"
                    )

                result = response_data.get("result", {})

                # Create and return an Execution object with the output data
                return Execution(output_data=result)
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to execute code: {e}")
