"""Set input value in a React-friendly way (clear + send_keys or native setter + events)."""
def safe_input(driver, element, text):
    if text is None:
        text = ""

    try:
        element.clear()
        element.send_keys(text)
        return
    except Exception:
        pass

    # React-safe setter
    driver.execute_script("""
        const element = arguments[0];
        const value = arguments[1];

        const nativeInputValueSetter =
            Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype,
                "value"
            ).set;

        nativeInputValueSetter.call(element, value);

        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
    """, element, text)