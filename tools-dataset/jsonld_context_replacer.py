"""Replace the top-level @context value in a selected JSON-LD file.

The app uses Tkinter's native file dialogs, which are available with most
standard Python installations on Windows, macOS, and Linux.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tkinter import Tk, filedialog, messagebox


TARGET_CONTEXT = "https://ofn.gov.cz/slovníky/draft/kontexty/slovníky.jsonld"
SUPPORTED_EXTENSIONS = {".jsonld", ".json-ld"}


def log(message: str) -> None:
    """Print a consistently formatted console log line."""
    print(f"[jsonld-context-replacer] {message}", flush=True)


def select_input_file() -> Path | None:
    log("Opening file selection dialog.")
    selected_file = filedialog.askopenfilename(
        title="Select JSON-LD file",
        filetypes=[
            ("JSON-LD files", "*.jsonld *.json-ld"),
            ("All files", "*.*"),
        ],
    )

    if not selected_file:
        log("No input file selected. Exiting.")
        return None

    input_path = Path(selected_file)
    log(f"Selected input file: {input_path}")
    return input_path


def validate_input_file(input_path: Path) -> bool:
    log("Validating selected file extension.")
    extension = input_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        log(
            "Unsupported file extension. Expected one of: "
            + ", ".join(sorted(SUPPORTED_EXTENSIONS))
        )
        messagebox.showerror(
            "Unsupported file type",
            "Please select a file with a .jsonld or .json-ld extension.",
        )
        return False

    log("File extension is supported.")
    return True


def load_json(input_path: Path) -> object:
    log("Reading selected file as UTF-8 JSON.")
    with input_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    log("JSON parsed successfully.")
    return data


def replace_context(data: object) -> bool:
    log("Checking for top-level @context key.")

    if not isinstance(data, dict):
        log("JSON root is not an object. No @context replacement was made.")
        return False

    if "@context" not in data:
        log("Top-level @context key was not found. No replacement was made.")
        return False

    old_value = data["@context"]
    data["@context"] = TARGET_CONTEXT
    log(f"Replaced @context value. Previous value was: {old_value!r}")
    log(f"New @context value is: {TARGET_CONTEXT!r}")
    return True


def select_output_file(input_path: Path) -> Path | None:
    default_name = f"{input_path.stem}_context_replaced{input_path.suffix}"
    log("Opening save file dialog.")
    selected_file = filedialog.asksaveasfilename(
        title="Save modified JSON-LD file",
        defaultextension=input_path.suffix,
        initialfile=default_name,
        filetypes=[
            ("JSON-LD files", "*.jsonld *.json-ld"),
            ("All files", "*.*"),
        ],
        confirmoverwrite=True,
    )

    if not selected_file:
        log("No output file selected. Exiting without saving.")
        return None

    output_path = Path(selected_file)
    log(f"Selected output file: {output_path}")
    return output_path


def save_json(output_path: Path, data: object) -> None:
    log("Writing modified JSON to output file.")
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")

    log("Output file written successfully.")


def main() -> int:
    log("Starting JSON-LD @context replacer.")

    root = Tk()
    root.withdraw()
    root.update()

    try:
        input_path = select_input_file()
        if input_path is None:
            return 0

        if not validate_input_file(input_path):
            return 1

        try:
            data = load_json(input_path)
        except OSError as error:
            log(f"Failed to read input file: {error}")
            messagebox.showerror("Read error", f"Could not read the selected file:\n{error}")
            return 1
        except json.JSONDecodeError as error:
            log(f"Failed to parse JSON: {error}")
            messagebox.showerror("JSON error", f"The selected file is not valid JSON:\n{error}")
            return 1

        replaced = replace_context(data)
        if not replaced:
            log("Continuing to save a copy of the parsed JSON.")

        output_path = select_output_file(input_path)
        if output_path is None:
            return 0

        try:
            save_json(output_path, data)
        except OSError as error:
            log(f"Failed to write output file: {error}")
            messagebox.showerror("Write error", f"Could not save the output file:\n{error}")
            return 1

        messagebox.showinfo("Done", f"Saved modified JSON-LD file to:\n{output_path}")
        log("Finished successfully.")
        return 0
    finally:
        log("Closing application window resources.")
        root.destroy()


if __name__ == "__main__":
    sys.exit(main())
