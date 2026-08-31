import { icons } from "@iconify-json/ph";
import { getIconData, iconToSVG } from "@iconify/utils";

export interface InlineIcon {
  body: string;
  viewBox: string;
}

/**
 * Resolve one Phosphor glyph from the official Iconify set at build time.
 * Islands receive plain markup, so no icon library ships to the browser.
 */
export function inlineIcon(name: string): InlineIcon {
  const data = getIconData(icons, name.replace(/^ph:/, ""));
  if (!data) throw new Error(`Unknown Phosphor icon: ${name}`);
  const rendered = iconToSVG(data);
  return { body: rendered.body, viewBox: rendered.attributes.viewBox };
}
