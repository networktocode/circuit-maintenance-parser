# Frequently Asked Questions

## Q: My provider is not supported. What can I do?

You can extend the library by adding a new provider. See the [Extending the Library](../dev/extending.md) guide for instructions. Pull requests for new providers are always welcome!

## Q: The parser for my provider is returning incorrect data. What should I do?

Please [open an issue](https://github.com/networktocode/circuit-maintenance-parser/issues/new) with the details. If possible, include a sanitized sample of the notification data that is being parsed incorrectly.

## Q: Can I use the LLM-powered parser without a specific provider?

Yes, the LLM-powered parsers are automatically appended after all existing processors for each defined Provider when the appropriate environment variables are set. You can use them with any provider, including the `GenericProvider`.

## Q: How do I check if a maintenance was parsed by an LLM?

Each `Maintenance` object has a `metadata` attribute. Check `maintenance.metadata.generated_by_llm` to determine if LLM parsing was used.

## Q: Where can I get help?

Feel free to swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#networktocode`). Sign up [here](http://slack.networktocode.com/) if you don't have an account.
