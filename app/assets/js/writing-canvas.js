/**
 * Writing Canvas Placeholder Behavior
 *
 * Makes the writing canvas placeholder text disappear on focus and reappear
 * when the canvas is empty, similar to HTML5 input placeholder behavior.
 */

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("writing-canvas");
    if (!canvas) return;

    const placeholderText =
        "Click here to add your own explanations, derivations, and notes about each integration scheme...";

    // Create and insert the placeholder span
    const placeholder = document.createElement("span");
    placeholder.className = "writing-canvas-placeholder";
    placeholder.style.color = "#8b949e";
    placeholder.style.fontStyle = "italic";
    placeholder.textContent = placeholderText;
    canvas.appendChild(placeholder);

    function updatePlaceholder() {
        // Hide placeholder if canvas has meaningful content
        const hasContent =
            canvas.textContent.trim().length > 0 &&
            canvas.textContent.trim() !== placeholderText;
        placeholder.style.display = hasContent ? "none" : "inline";
    }

    // Hide placeholder on focus
    canvas.addEventListener("focus", function () {
        placeholder.style.display = "none";
    });

    // Re-evaluate placeholder on blur
    canvas.addEventListener("blur", updatePlaceholder);

    // Update placeholder as user types
    canvas.addEventListener("input", updatePlaceholder);

    // Initial state
    updatePlaceholder();
});
