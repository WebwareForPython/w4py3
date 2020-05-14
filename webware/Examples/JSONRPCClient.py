"""JSON-RPC demo client contributed by Christoph Zwerschke"""

from .ExamplePage import ExamplePage


class JSONRPCClient(ExamplePage):
    """Demo client for using the JSON-RPC example."""

    def writeJavaScript(self):
        ExamplePage.writeJavaScript(self)
        self.write('''\
            <script src="jsonrpc.js"></script>
            <script>
            jsonrpc = new JSONRpcClient("JSONRPCExample");
            methods = jsonrpc.system.listMethods();
            function dojsonrpc() {
                p = document.getElementById("parameter").value;
                i = document.getElementById("method").selectedIndex;
                r = jsonrpc[methods[i]](p);
                document.getElementById("result").value = r;
            }
            </script>
        ''')

    def writeContent(self):
        self.write('''\
            <h3>JSON-RPC Example</h3>
            <p>This example shows how you can call methods
            of a <a href="https://www.jsonrpc.org/">JSON-RPC</a> servlet
            built with Webware for Python from your web browser
            via JavaScript (which has to be activated to run this demo).
            <noscript><span style="color:red">
            Unfortunately, JavaScript is not activated.
            </span></noscript></p>
            <p>The example uses a JSON-RPC JavaScript client
            based on Jan-Klaas' "JavaScript o lait" library.</p>
            <p>Type in any example text to be used as input parameter,
            choose one of the available methods to be invoked by the
            example servlet and press the button to display the result.</p>
            <table>
            <tr style="text-align:center">
            <th>Input parameter</th>
            <th>Remote method</th>
            <th>Result</th>
            </tr><tr style="text-align:center">
            <td>
            <input id="parameter" type="text" size="20" value="Hello, World!">
            </td><td>
            <select id="method" size="1">
            <script>
            for (m in methods)
                document.writeln('<option>' + methods[m] + '</option>');
            </script>
            </select>
            </td><td>
            <input type="text" size="20" id="result">
            </td>
            </tr><tr style="text-align:center">
            <td colspan="3">
            <input type="button" value="Invoke remote method"
                onclick="dojsonrpc()">
            </td>
            </tr>
            </table>
        ''')
