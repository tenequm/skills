# Component Patterns Reference

## Composition with asChild

Use `asChild` to compose components without wrapper divs:

```tsx
// Button as a Link (Next.js)
import Link from "next/link"

<Button asChild>
  <Link href="/login">Login</Link>
</Button>

// Renders: <a href="/login" class="...button classes">Login</a>
// No wrapper div!

// Button as a custom component
<Button asChild variant="outline">
  <a href="https://example.com" target="_blank">
    External Link
  </a>
</Button>

// Dialog trigger with custom element
<DialogTrigger asChild>
  <div className="cursor-pointer">
    Custom trigger element
  </div>
</DialogTrigger>
```

**When to use:**
- Wrapping navigation links
- Custom interactive elements
- Avoiding nested buttons
- Semantic HTML (button → link when navigating)

## Typography Patterns

shadcn/ui typography scales using Tailwind utilities:

```tsx
// Headings with responsive sizing
<h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl">
  Taxing Laughter: The Joke Tax Chronicles
</h1>

<h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0">
  The People of the Kingdom
</h2>

<h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">
  The Joke Tax
</h3>

<h4 className="scroll-m-20 text-xl font-semibold tracking-tight">
  People stopped telling jokes
</h4>

// Paragraph
<p className="leading-7 [&:not(:first-child)]:mt-6">
  The king, seeing how much happier his subjects were, realized the error of his ways.
</p>

// Blockquote
<blockquote className="mt-6 border-l-2 pl-6 italic">
  "After all," he said, "everyone enjoys a good joke."
</blockquote>

// Inline code
<code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold">
  @radix-ui/react-alert-dialog
</code>

// Lead text (larger paragraph)
<p className="text-xl text-muted-foreground">
  A modal dialog that interrupts the user with important content.
</p>

// Small text
<small className="text-sm font-medium leading-none">Email address</small>

// Muted text
<p className="text-sm text-muted-foreground">
  Enter your email address.
</p>

// List
<ul className="my-6 ml-6 list-disc [&>li]:mt-2">
  <li>1st level of puns: 5 gold coins</li>
  <li>2nd level of jokes: 10 gold coins</li>
  <li>3rd level of one-liners: 20 gold coins</li>
</ul>
```

## Icons with Lucide

```tsx
import { ChevronRight, Check, X, AlertCircle, Loader2 } from "lucide-react"

// Icon sizing with components
<Button>
  <ChevronRight className="size-4" />
  Next
</Button>

// Icons automatically adjust to button size
<Button size="sm">
  <Check className="size-4" />
  Small Button
</Button>

<Button size="lg">
  <Check className="size-4" />
  Large Button
</Button>

// Icon-only button
<Button size="icon" variant="outline">
  <X className="size-4" />
</Button>

// Loading state
<Button disabled>
  <Loader2 className="size-4 animate-spin" />
  Please wait
</Button>

// Icon with semantic colors
<AlertCircle className="size-4 text-destructive" />
<Check className="size-4 text-success" />

// In alerts
<Alert>
  <AlertCircle className="size-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>
    Your session has expired.
  </AlertDescription>
</Alert>
```

**Icon sizing reference:**
- `size-3` - Extra small (12px)
- `size-4` - Small/default (16px)
- `size-5` - Medium (20px)
- `size-6` - Large (24px)

## Form with React Hook Form

Complete form example with validation:

```tsx
"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"

// Define schema
const formSchema = z.object({
  username: z.string().min(2, {
    message: "Username must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  bio: z.string().max(160).min(4),
})

export function ProfileForm() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      email: "",
      bio: "",
    },
  })

  function onSubmit(values: z.infer<typeof formSchema>) {
    toast.success("Profile updated successfully")
    console.log(values)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="shadcn" {...field} />
              </FormControl>
              <FormDescription>
                This is your public display name.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="m@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="bio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bio</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Tell us about yourself"
                  className="resize-none"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                You can write up to 160 characters.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit">Update profile</Button>
      </form>
    </Form>
  )
}
```

## Input Variants

### Input OTP

```tsx
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSeparator,
  InputOTPSlot,
} from "@/components/ui/input-otp"

<InputOTP maxLength={6}>
  <InputOTPGroup>
    <InputOTPSlot index={0} />
    <InputOTPSlot index={1} />
    <InputOTPSlot index={2} />
  </InputOTPGroup>
  <InputOTPSeparator />
  <InputOTPGroup>
    <InputOTPSlot index={3} />
    <InputOTPSlot index={4} />
    <InputOTPSlot index={5} />
  </InputOTPGroup>
</InputOTP>
```

### Input with Icon

```tsx
import { Search } from "lucide-react"

<div className="relative">
  <Search className="absolute left-2 top-2.5 size-4 text-muted-foreground" />
  <Input placeholder="Search" className="pl-8" />
</div>
```

### File Input

```tsx
<Input
  type="file"
  className="cursor-pointer file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-semibold file:text-primary-foreground hover:file:bg-primary/90"
/>
```

### Input Group

```tsx
import { InputGroup, InputGroupText } from "@/components/ui/input-group"

<InputGroup>
  <InputGroupText>https://</InputGroupText>
  <Input placeholder="example.com" />
</InputGroup>

<InputGroup>
  <Input placeholder="Amount" />
  <InputGroupText>USD</InputGroupText>
</InputGroup>
```

## Component Authoring Pattern

All shadcn/ui components use plain functions with `data-slot` attributes (React 19):

```tsx
// Modern pattern - no forwardRef, no displayName
function AccordionItem({
  className,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Item>) {
  return (
    <AccordionPrimitive.Item
      data-slot="accordion-item"
      className={cn("border-b last:border-b-0", className)}
      {...props}
    />
  )
}

// Parent-level styling via data-slot selectors
<div className="*:data-[slot=avatar]:ring-2 *:data-[slot=description]:text-sm">
  <Avatar data-slot="avatar" />
  <p data-slot="description">Styled by parent</p>
</div>
```

**Key changes from older patterns:**
- `React.forwardRef` removed (React 19 passes ref as regular prop)
- `React.ComponentPropsWithoutRef` replaced by `React.ComponentProps`
- `displayName` removed
- Every primitive gets a `data-slot` attribute

**Common data-slot values:**
- `icon` - Icons within components
- `button`, `trigger` - Interactive elements
- `title`, `description` - Text elements
- `content`, `header`, `footer` - Layout sections

## Data-Icon Attributes

Buttons use `data-icon` for automatic icon spacing:

```tsx
// Icons get correct spacing automatically
<Button>
  <Spinner data-icon="inline-start" />
  Generating...
</Button>

<Button>
  Submit
  <ArrowRight data-icon="inline-end" />
</Button>

// data-slot="icon" also works for simple icon buttons
<Button>
  <CheckIcon data-slot="icon" />
  Save Changes
</Button>
```

## Select Component

```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

<Select>
  <SelectTrigger className="w-[180px]">
    <SelectValue placeholder="Select a fruit" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="apple">Apple</SelectItem>
    <SelectItem value="banana">Banana</SelectItem>
    <SelectItem value="blueberry">Blueberry</SelectItem>
  </SelectContent>
</Select>

// With form
<FormField
  control={form.control}
  name="fruit"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Fruit</FormLabel>
      <Select onValueChange={field.onChange} defaultValue={field.value}>
        <FormControl>
          <SelectTrigger>
            <SelectValue placeholder="Select a fruit" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          <SelectItem value="apple">Apple</SelectItem>
          <SelectItem value="banana">Banana</SelectItem>
        </SelectContent>
      </Select>
      <FormMessage />
    </FormItem>
  )}
/>
```

## Checkbox and Radio Groups

```tsx
// Checkbox
import { Checkbox } from "@/components/ui/checkbox"

<div className="flex items-center space-x-2">
  <Checkbox id="terms" />
  <label
    htmlFor="terms"
    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
  >
    Accept terms and conditions
  </label>
</div>

// Radio Group
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

<RadioGroup defaultValue="comfortable">
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="default" id="r1" />
    <Label htmlFor="r1">Default</Label>
  </div>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="comfortable" id="r2" />
    <Label htmlFor="r2">Comfortable</Label>
  </div>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="compact" id="r3" />
    <Label htmlFor="r3">Compact</Label>
  </div>
</RadioGroup>
```

## Dialog Pattern

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog"

<Dialog>
  <DialogTrigger asChild>
    <Button variant="outline">Edit Profile</Button>
  </DialogTrigger>
  <DialogContent className="sm:max-w-[425px]">
    <DialogHeader>
      <DialogTitle>Edit profile</DialogTitle>
      <DialogDescription>
        Make changes to your profile here. Click save when you're done.
      </DialogDescription>
    </DialogHeader>
    <div className="grid gap-4 py-4">
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="name" className="text-right">
          Name
        </Label>
        <Input id="name" value="Pedro Duarte" className="col-span-3" />
      </div>
    </div>
    <DialogFooter>
      <Button type="submit">Save changes</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

## Dropdown Menu

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline">Open</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>My Account</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem>Profile</DropdownMenuItem>
    <DropdownMenuItem>Billing</DropdownMenuItem>
    <DropdownMenuItem>Team</DropdownMenuItem>
    <DropdownMenuItem>Subscription</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

## Toast Notifications

```tsx
import { toast } from "sonner"

// Success
toast.success("Event created successfully")

// Error
toast.error("Something went wrong")

// Info
toast.info("Be aware that...")

// Warning
toast.warning("Proceed with caution")

// Loading
toast.loading("Uploading...")

// Custom
toast("Event created", {
  description: "Monday, January 3rd at 6:00pm",
  action: {
    label: "Undo",
    onClick: () => console.log("Undo"),
  },
})

// Promise
toast.promise(promise, {
  loading: "Loading...",
  success: (data) => `${data.name} created`,
  error: "Error creating event",
})
```

## Data Table Pattern

```tsx
"use client"

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
}

export function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {flexRender(
                    header.column.columnDef.header,
                    header.getContext()
                  )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
```

## CLI Commands Reference

```bash
# Create new project (interactive - choose style, primitives, colors)
npx shadcn create

# Initialize in existing project
pnpm dlx shadcn@latest init

# Add components
pnpm dlx shadcn@latest add button
pnpm dlx shadcn@latest add card form input

# Add all components
pnpm dlx shadcn@latest add --all

# Add from community registries
npx shadcn add @acme/button @internal/auth-system

# View/search/list registries
npx shadcn view @acme/auth-system
npx shadcn search @tweakcn -q "dark"
npx shadcn list @acme

# Update/overwrite existing components
pnpm dlx shadcn@latest add button --overwrite
pnpm dlx shadcn@latest add --all --overwrite

# Show component diff (see what changed)
pnpm dlx shadcn@latest diff button

# Add MCP server for AI agent integration
npx shadcn@latest mcp init
```

### Namespaced Registries

Configure private or community registries in `components.json`:

```json
{
  "registries": {
    "@acme": "https://acme.com/r/{name}.json",
    "@internal": {
      "url": "https://registry.company.com/{name}",
      "headers": {
        "Authorization": "Bearer ${REGISTRY_TOKEN}"
      }
    }
  }
}
```

## Field Component (October 2025)

Composable form field wrapper - works with React Hook Form, TanStack Form, Server Actions, or any form library:

```tsx
import {
  Field, FieldLabel, FieldDescription, FieldError,
  FieldSet, FieldGroup, FieldLegend, FieldSeparator,
  FieldContent, FieldTitle,
} from "@/components/ui/field"

// Basic field
<Field>
  <FieldLabel>Email address</FieldLabel>
  <Input type="email" placeholder="m@example.com" />
  <FieldDescription>We'll never share your email.</FieldDescription>
  <FieldError>{errors.email?.message}</FieldError>
</Field>

// With validation state
<Field invalid={!!errors.password}>
  <FieldLabel required>Password</FieldLabel>
  <Input type="password" />
  <FieldError>{errors.password?.message}</FieldError>
</Field>

// Responsive orientation (auto-switches by container width)
<Field orientation="responsive">
  <FieldContent>
    <FieldLabel htmlFor="msg">Message</FieldLabel>
    <FieldDescription>Keep it short</FieldDescription>
  </FieldContent>
  <Textarea id="msg" placeholder="Hello" />
</Field>

// Field sets for grouped fields
<FieldSet>
  <FieldLegend>Payment Method</FieldLegend>
  <FieldDescription>All transactions are secure</FieldDescription>
  <FieldGroup>
    <Field>
      <FieldLabel htmlFor="name">Name on Card</FieldLabel>
      <Input id="name" placeholder="Evil Rabbit" required />
    </Field>
    <Field>
      <FieldLabel htmlFor="number">Card Number</FieldLabel>
      <Input id="number" placeholder="4242..." required />
    </Field>
  </FieldGroup>
</FieldSet>

// Selectable choice cards (FieldLabel wrapping)
<Field>
  <FieldLabel className="flex cursor-pointer items-center gap-3 rounded-lg border p-4 has-[:checked]:border-primary">
    <RadioGroupItem value="card" />
    <div>
      <FieldTitle>Credit Card</FieldTitle>
      <FieldDescription>Pay with Visa or Mastercard</FieldDescription>
    </div>
  </FieldLabel>
</Field>
```

## Item Component (October 2025)

Flexible container for lists, cards, and navigation:

```tsx
import {
  Item, ItemMedia, ItemContent, ItemTitle,
  ItemDescription, ItemActions, ItemGroup, ItemSeparator,
} from "@/components/ui/item"

// List item with icon and actions
<Item>
  <ItemMedia variant="icon">
    <FileIcon className="size-4" />
  </ItemMedia>
  <ItemContent>
    <ItemTitle>document.pdf</ItemTitle>
    <ItemDescription>2.4 MB</ItemDescription>
  </ItemContent>
  <ItemActions>
    <Button variant="ghost" size="icon">
      <MoreHorizontal className="size-4" />
    </Button>
  </ItemActions>
</Item>

// Card-style navigation
<Item asChild>
  <a href="/dashboard" className="rounded-lg border p-4 hover:bg-accent">
    <ItemMedia variant="icon">
      <LayoutDashboard className="size-5" />
    </ItemMedia>
    <ItemContent>
      <ItemTitle>Dashboard</ItemTitle>
      <ItemDescription>View your analytics</ItemDescription>
    </ItemContent>
  </a>
</Item>

// Grouped items with separators
<ItemGroup>
  <Item asChild>
    <a href="/home" className="px-3 py-2 rounded-md hover:bg-accent">
      <ItemMedia variant="icon"><Home className="size-4" /></ItemMedia>
      <ItemContent><ItemTitle>Home</ItemTitle></ItemContent>
    </a>
  </Item>
  <ItemSeparator />
  <Item asChild>
    <a href="/settings" className="px-3 py-2 rounded-md hover:bg-accent">
      <ItemMedia variant="icon"><Settings className="size-4" /></ItemMedia>
      <ItemContent><ItemTitle>Settings</ItemTitle></ItemContent>
    </a>
  </Item>
</ItemGroup>
```

## Spinner Component (October 2025)

Dedicated loading spinner component:

```tsx
import { Spinner } from "@/components/ui/spinner"

// Default spinner
<Spinner />

// With size variants
<Spinner size="sm" />
<Spinner size="md" />
<Spinner size="lg" />

// In buttons
<Button disabled>
  <Spinner size="sm" />
  Loading...
</Button>

// Full page loading
<div className="flex min-h-screen items-center justify-center">
  <Spinner size="lg" />
</div>

// With custom colors
<Spinner className="text-primary" />
```

## Button Group (October 2025)

Grouped buttons with consistent styling:

```tsx
import { ButtonGroup, ButtonGroupButton } from "@/components/ui/button-group"

// Basic button group
<ButtonGroup>
  <ButtonGroupButton>Left</ButtonGroupButton>
  <ButtonGroupButton>Center</ButtonGroupButton>
  <ButtonGroupButton>Right</ButtonGroupButton>
</ButtonGroup>

// With active state
<ButtonGroup>
  <ButtonGroupButton active>Day</ButtonGroupButton>
  <ButtonGroupButton>Week</ButtonGroupButton>
  <ButtonGroupButton>Month</ButtonGroupButton>
</ButtonGroup>

// With icons
<ButtonGroup>
  <ButtonGroupButton>
    <Bold className="size-4" />
  </ButtonGroupButton>
  <ButtonGroupButton>
    <Italic className="size-4" />
  </ButtonGroupButton>
  <ButtonGroupButton>
    <Underline className="size-4" />
  </ButtonGroupButton>
</ButtonGroup>

// Vertical orientation
<ButtonGroup orientation="vertical">
  <ButtonGroupButton>Top</ButtonGroupButton>
  <ButtonGroupButton>Middle</ButtonGroupButton>
  <ButtonGroupButton>Bottom</ButtonGroupButton>
</ButtonGroup>
```

## Keyboard Shortcuts Component

```tsx
import { Kbd } from "@/components/ui/kbd"

<div className="flex items-center gap-1">
  <Kbd>⌘</Kbd>
  <Kbd>K</Kbd>
</div>

// Search shortcut display
<div className="text-sm text-muted-foreground">
  Press <Kbd>⌘</Kbd> + <Kbd>K</Kbd> to search
</div>
```

## Empty State

```tsx
import { Empty, EmptyMedia, EmptyTitle, EmptyDescription, EmptyContent, EmptyHeader } from "@/components/ui/empty"
import { FileIcon } from "lucide-react"

<Empty>
  <EmptyMedia>
    <FileIcon className="size-10 text-muted-foreground" />
  </EmptyMedia>
  <EmptyHeader>
    <EmptyTitle>No files uploaded</EmptyTitle>
    <EmptyDescription>Upload your first file to get started</EmptyDescription>
  </EmptyHeader>
  <EmptyContent>
    <Button>Upload File</Button>
  </EmptyContent>
</Empty>
```

## RTL / Direction Support (January 2026)

```tsx
import { Direction } from "@/components/ui/direction"

// Wrap app or section for RTL support
<Direction dir="rtl">
  <App />
</Direction>

// Components automatically adapt layout direction
// Use Tailwind logical properties for RTL-aware styling:
<div className="ps-4 pe-2 ms-auto">  {/* start/end instead of left/right */}
```

Tailwind v4.2 logical properties (`pbs-*`, `pbe-*`, `mbs-*`, `mbe-*`, `inset-s-*`, `inset-e-*`) provide full RTL support at the utility level.

## Common Pitfalls

### Form `defaultValues` Required

Always provide `defaultValues` in `useForm()` - omitting them causes uncontrolled-to-controlled warnings and broken validation:

```tsx
// CORRECT
const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { name: "", email: "", age: 0 },
})

// WRONG - missing defaultValues
const form = useForm({ resolver: zodResolver(schema) })
```

Use `z.coerce.number()` for numeric inputs (HTML inputs always return strings):
```tsx
const schema = z.object({
  age: z.coerce.number().min(0).max(150),
  price: z.coerce.number().positive(),
})
```

### Select and Switch in Forms

Select uses `onValueChange` (not `onChange`). Switch uses `onCheckedChange` and `checked`:

```tsx
// Select - wire onChange to onValueChange
<Select onValueChange={field.onChange} defaultValue={field.value}>

// Switch - wire both checked and onCheckedChange
<Switch checked={field.value} onCheckedChange={field.onChange} />
```

### Never Nest Dialogs

Nested `<Dialog>` components break focus trapping. Use state machine pattern instead:

```tsx
// WRONG - nested dialogs
<Dialog>
  <DialogContent>
    <Dialog>  {/* breaks focus trap */}
      <DialogContent>...</DialogContent>
    </Dialog>
  </DialogContent>
</Dialog>

// CORRECT - state machine
const [view, setView] = useState<"list" | "confirm" | null>(null)

<Dialog open={view === "list"} onOpenChange={() => setView(null)}>
  <DialogContent>
    <Button onClick={() => { setView("confirm") }}>Delete</Button>
  </DialogContent>
</Dialog>

<Dialog open={view === "confirm"} onOpenChange={() => setView(null)}>
  <DialogContent>Are you sure?</DialogContent>
</Dialog>
```

### Sticky Positioning

`position: sticky` fails silently if any ancestor has `overflow: hidden` or `overflow: auto`:

```tsx
// WRONG - sticky won't work inside overflow container
<div className="overflow-auto">
  <div className="sticky top-0">Never sticks</div>
</div>

// CORRECT - sticky element must be direct child of scroll container
<div className="overflow-auto">
  <div className="sticky top-0 z-10 bg-background">Table header</div>
  <div>Scrollable content</div>
</div>
```

### Server vs Client Components

Never add `"use client"` to shadcn/ui source files. Instead, wrap interactive parts:

```tsx
// WRONG - making the whole page client-side
"use client"
export default function Page() { ... }

// CORRECT - isolate client components, pass server data as children
export default function Page() {
  const data = await getData()
  return (
    <ClientWrapper>
      <ServerContent data={data} />
    </ClientWrapper>
  )
}
```

### Tooling

Install these for consistent code quality:

```bash
# Auto-sorts Tailwind classes in canonical order
pnpm add -D prettier-plugin-tailwindcss

# Lints class usage (no contradictions, no deprecated utilities)
pnpm add -D eslint-plugin-tailwindcss
```
