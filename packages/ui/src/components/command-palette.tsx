"use client";
import { Command } from "cmdk";
import * as React from "react";

export interface CommandItem { id: string; label: string; hint?: string }
export interface CommandPaletteProps {
  items: CommandItem[];
  onSelect: (item: CommandItem) => void;
}

export function CommandPalette({ items, onSelect }: CommandPaletteProps) {
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
    <Command.Dialog open={open} onOpenChange={setOpen} label="Command palette">
      <Command.Input placeholder="Search drivers, races, sessions" />
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
