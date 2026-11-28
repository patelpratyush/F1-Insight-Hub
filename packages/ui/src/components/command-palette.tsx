"use client";
import { Command } from "cmdk";
import * as React from "react";

export interface CommandItem { id: string; label: string; hint?: string }
export interface CommandPaletteProps {
  items: CommandItem[];
  onSelect: (item: CommandItem) => void;
  /** When set, items are already filtered (e.g. by a server search) and cmdk does not filter them again. */
  onQueryChange?: (query: string) => void;
}

export function CommandPalette({ items, onSelect, onQueryChange }: CommandPaletteProps) {
  const [open, setOpen] = React.useState(false);
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);
  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      shouldFilter={!onQueryChange}
      overlayClassName="fixed inset-0 bg-black/70"
      contentClassName="fixed left-1/2 top-24 w-[min(36rem,92vw)] -translate-x-1/2 rounded-[var(--radius-card)] border border-carbon-700 bg-carbon-900 p-2 [&_[cmdk-input]]:w-full [&_[cmdk-input]]:bg-transparent [&_[cmdk-input]]:p-3 [&_[cmdk-input]]:outline-none [&_[cmdk-item]]:flex [&_[cmdk-item]]:rounded [&_[cmdk-item]]:px-3 [&_[cmdk-item]]:py-2 [&_[cmdk-item][data-selected=true]]:bg-carbon-800 [&_[cmdk-empty]]:p-3 [&_[cmdk-empty]]:text-carbon-500"
    >
      <Command.Input placeholder="Search drivers, races, sessions" {...(onQueryChange ? { onValueChange: onQueryChange } : {})} />
      <Command.List>
        <Command.Empty>No results.</Command.Empty>
        {items.map((item) => (
          <Command.Item key={item.id} value={item.label} onSelect={() => { onSelect(item); setOpen(false); }}>
            {item.label}
            {item.hint ? <span className="ml-auto text-carbon-500">{item.hint}</span> : null}
          </Command.Item>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}
