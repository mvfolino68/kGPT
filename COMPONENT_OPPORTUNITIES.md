# Component Extraction Opportunities

## 1. **LoadingState Component**

**Pattern:** Simple "Loading..." text with optional spinner
**Found in:**

- `ChatHistory.svelte` - "Loading..." text
- `KafkaSection.svelte` - "Loading..." text
- `DocumentsTable.svelte` - "Loading..." with animate-pulse
- `dashboard/+page.svelte` - Loading spinner with text

**Proposed Component:**

```svelte
<LoadingState message="Loading..." showSpinner={true} />
```

---

## 2. **EmptyState Component**

**Pattern:** Icon + message + optional description
**Found in:**

- `ChatHistory.svelte` - "No sessions yet"
- `ConsumerGroupsPanel.svelte` - "No consumer groups" with icon
- `BrokersGrid.svelte` - "No brokers available"
- `AgentTracePanel.svelte` - "No activity yet"
- `AgentActivitySidebar.svelte` - "No agent activity yet"
- `DocumentsTable.svelte` - Empty state with icon

**Proposed Component:**

```svelte
<EmptyState
  icon="users"
  title="No sessions yet"
  description="Start a new chat to begin"
/>
```

---

## 3. **LoadingSpinner Component**

**Pattern:** SVG spinner animation repeated in multiple places
**Found in:**

- `Button.svelte` - Loading spinner
- `dashboard/+page.svelte` - Loading spinner
- `ClusterStep.svelte` - Loading spinner
- Multiple other places

**Proposed Component:**

```svelte
<LoadingSpinner size="sm" class="text-primary" />
```

---

## 4. **StatusMessage Component** (Error/Success/Info)

**Pattern:** Status pill + message text
**Found in:**

- `OperationError.svelte` - Error card pattern
- `OperationSuccess.svelte` - Success card pattern
- `dashboard/+page.svelte` - Error display
- `documents/+page.svelte` - Error/success messages

**Proposed Component:**

```svelte
<StatusMessage
  variant="error"
  title="Operation Failed"
  message={error}
  dismissable
/>
```

---

## 5. **SearchInput Component**

**Pattern:** Input with search icon
**Found in:**

- `TopicsPanel.svelte` - Search input
- `ConsumerGroupsPanel.svelte` - Search input
- Multiple other panels

**Note:** Already using `Input` with icon slot, but could standardize pattern

---

## 6. **ConfirmDialog Component**

**Pattern:** Confirmation UI with "confirm delete" text input
**Found in:**

- `SyncStatusPanel.svelte` - Multiple confirmation dialogs
- `PendingConfirmation.svelte` - Confirmation pattern
- Similar patterns in other destructive operations

**Proposed Component:**

```svelte
<ConfirmDialog
  variant="danger"
  title="Delete Orphans"
  message="This will permanently delete..."
  confirmText="confirm delete"
  onConfirm={handleConfirm}
  onCancel={handleCancel}
/>
```

---

## 7. **Badge/Pill Variants**

**Pattern:** Custom badge classes for status colors
**Found in:**

- `TopicsPanel.svelte` - `getReplicationBadgeClass()`
- `ConsumerGroupsPanel.svelte` - `getStateBadgeClass()`
- Multiple other places with similar badge logic

**Note:** `StatusPill` exists but custom badge logic is repeated

---

## 8. **SectionHeader Component**

**Pattern:** Icon + title + optional action
**Found in:**

- `OperationHeader.svelte` - Already a component!
- Similar patterns in other admin components

**Status:** Already extracted ✓

---

## 9. **DataRow/KeyValueRow Component**

**Pattern:** Key-value pairs in config displays
**Found in:**

- `ConfigList.svelte` - Key-value rows
- `OperationSuccess.svelte` - Data entries
- Multiple admin components

**Proposed Component:**

```svelte
<DataRow label="Key" value="Value" color="green" />
```

---

## 10. **Backdrop/Overlay Component**

**Pattern:** Modal/drawer backdrop
**Found in:**

- `ChatDrawer.svelte` - Backdrop div
- `CitationModal.svelte` - Backdrop div
- `AgentTraceDrawer.svelte` - Backdrop div

**Proposed Component:**

```svelte
<Backdrop onClose={onClose} />
```

---

## Priority Recommendations

1. **LoadingState** - High impact, used everywhere
2. **EmptyState** - High impact, consistent UX
3. **LoadingSpinner** - Medium impact, reduces duplication
4. **StatusMessage** - Medium impact, standardizes error/success displays
5. **ConfirmDialog** - Medium impact, improves destructive operation UX
