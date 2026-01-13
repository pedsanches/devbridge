import type { Meta, StoryObj } from "@storybook/react";
import React from "react";

/**
 * Design System Documentation
 *
 * This story showcases the DevBridge design tokens and visual identity.
 */

const ColorSwatch = ({ name, value, textColor = "white" }: { name: string; value: string; textColor?: string }) => (
  <div className="flex items-center gap-3 mb-2">
    <div
      className="w-12 h-12 rounded-lg shadow-md flex items-center justify-center text-xs font-mono"
      style={{ backgroundColor: value, color: textColor }}
    >
      {value}
    </div>
    <div>
      <div className="font-medium">{name}</div>
      <div className="text-sm text-neutral-500">{value}</div>
    </div>
  </div>
);

const TypographySample = ({ size, label }: { size: string; label: string }) => (
  <div className="mb-4 pb-4 border-b border-neutral-200">
    <div className={`text-${size} font-semibold mb-1`}>The quick brown fox jumps</div>
    <div className="text-sm text-neutral-500">{label} — text-{size}</div>
  </div>
);

const SpacingBox = ({ size, value }: { size: string; value: string }) => (
  <div className="flex items-center gap-3 mb-2">
    <div
      className="bg-primary rounded"
      style={{ width: value, height: value }}
    />
    <div className="text-sm">
      <span className="font-mono">space-{size}</span> = {value}
    </div>
  </div>
);

// Main Design System component
const DesignSystem = () => {
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-2">DevBridge Design System</h1>
      <p className="text-neutral-500 mb-8">Visual identity and design tokens documentation</p>

      {/* Logo */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Logo</h2>
        <div className="flex gap-8">
          <div className="p-6 bg-white rounded-xl shadow-md">
            <img src="/logo.png" alt="DevBridge Logo" className="h-16" />
            <p className="text-sm text-neutral-500 mt-2">Light background</p>
          </div>
          <div className="p-6 bg-neutral-900 rounded-xl shadow-md">
            <img src="/logo.png" alt="DevBridge Logo" className="h-16" />
            <p className="text-sm text-neutral-400 mt-2">Dark background</p>
          </div>
        </div>
      </section>

      {/* Colors */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Color Palette</h2>

        <h3 className="text-lg font-medium mb-3">Primary</h3>
        <div className="grid grid-cols-2 gap-4 mb-6">
          <ColorSwatch name="Primary" value="#0071E3" />
          <ColorSwatch name="Primary Hover" value="#0077ED" />
        </div>

        <h3 className="text-lg font-medium mb-3">Semantic</h3>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <ColorSwatch name="Success" value="#30A46C" />
          <ColorSwatch name="Warning" value="#F5A623" textColor="black" />
          <ColorSwatch name="Error" value="#E5484D" />
        </div>

        <h3 className="text-lg font-medium mb-3">Neutral Scale</h3>
        <div className="grid grid-cols-5 gap-2">
          {[
            { name: "50", value: "#FAFAFA", text: "black" },
            { name: "100", value: "#F5F5F7", text: "black" },
            { name: "200", value: "#E8E8ED", text: "black" },
            { name: "300", value: "#D2D2D7", text: "black" },
            { name: "400", value: "#86868B", text: "white" },
            { name: "500", value: "#6E6E73", text: "white" },
            { name: "600", value: "#515154", text: "white" },
            { name: "700", value: "#3A3A3C", text: "white" },
            { name: "800", value: "#2C2C2E", text: "white" },
            { name: "900", value: "#1D1D1F", text: "white" },
          ].map((c) => (
            <div
              key={c.name}
              className="h-16 rounded-lg flex items-end p-2"
              style={{ backgroundColor: c.value, color: c.text }}
            >
              <span className="text-xs font-mono">{c.name}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Typography */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Typography</h2>
        <div className="space-y-4">
          <div className="text-4xl font-bold">Heading 1 — text-4xl</div>
          <div className="text-3xl font-bold">Heading 2 — text-3xl</div>
          <div className="text-2xl font-semibold">Heading 3 — text-2xl</div>
          <div className="text-xl font-semibold">Heading 4 — text-xl</div>
          <div className="text-lg">Lead text — text-lg</div>
          <div className="text-base">Body text — text-base</div>
          <div className="text-sm text-neutral-500">Secondary — text-sm</div>
          <div className="text-xs text-neutral-400">Caption — text-xs</div>
        </div>
      </section>

      {/* Spacing */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Spacing</h2>
        <div className="grid grid-cols-2 gap-4">
          <SpacingBox size="1" value="4px" />
          <SpacingBox size="2" value="8px" />
          <SpacingBox size="3" value="12px" />
          <SpacingBox size="4" value="16px" />
          <SpacingBox size="5" value="24px" />
          <SpacingBox size="6" value="32px" />
        </div>
      </section>

      {/* Border Radius */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Border Radius</h2>
        <div className="flex gap-4">
          {[
            { name: "sm", value: "6px" },
            { name: "md", value: "10px" },
            { name: "lg", value: "14px" },
            { name: "xl", value: "20px" },
            { name: "full", value: "9999px" },
          ].map((r) => (
            <div key={r.name} className="text-center">
              <div
                className="w-16 h-16 bg-primary mb-2"
                style={{ borderRadius: r.value }}
              />
              <div className="text-xs font-mono">{r.name}</div>
              <div className="text-xs text-neutral-400">{r.value}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Shadows */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Shadows</h2>
        <div className="flex gap-6">
          {["sm", "md", "lg", "xl"].map((s) => (
            <div key={s} className="text-center">
              <div className={`w-20 h-20 bg-white rounded-lg shadow-${s} mb-2`} />
              <div className="text-xs font-mono">shadow-{s}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

const meta: Meta<typeof DesignSystem> = {
  title: "Design System/Overview",
  component: DesignSystem,
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: "Complete overview of the DevBridge design system including colors, typography, spacing, and more.",
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof DesignSystem>;

export const Overview: Story = {};
