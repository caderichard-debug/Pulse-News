import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type FilterSelectOption = {
  value: string;
  label: string;
};

export function FilterSelect({
  id,
  label,
  value,
  onValueChange,
  options,
  triggerClassName,
}: {
  id?: string;
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  options: FilterSelectOption[];
  triggerClassName?: string;
}) {
  return (
    <label className="flex items-center gap-2 text-muted-foreground">
      <span className="uppercase tracking-wide text-xs">{label}</span>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger id={id} className={triggerClassName}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
