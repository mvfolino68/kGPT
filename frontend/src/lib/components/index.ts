// UI Components (design system)
export {
	Button,
	Card,
	Input,
	Select,
	Textarea,
	Badge,
	StatusDot,
	StatusPill,
	Tooltip,
	NavLink,
	ListItem,
	Icon,
	IconButton,
	DeleteButton,
	LoadingState,
	Panel,
	ClickableCard
} from './ui';

// Layout Components
export { Sidebar, Header, HeaderStatus } from './layout';

// Admin Components
export {
	AdminResultCard,
	PendingConfirmation,
	NeedsInfoForm,
	UnclearOperation,
	TopicsTable,
	TopicDetails,
	ConsumerGroupsTable,
	ConsumerGroupDetails,
	ClusterOverview,
	OffsetsTable,
	OperationSuccess,
	OperationError,
	OperationHeader,
	DataTable,
	ConfigList,
	CodePreview
} from './admin';
export * from './admin/types';

// Agent Trace Components
export { AgentTimelineItem, RoutingDecisionCard, RetrievalResultsList, WebResultsList } from './agent-trace';
export * from './agent-trace/types';

// Shared Components
export { default as CodeBlock } from './CodeBlock.svelte';
export { default as FormattedMessage } from './FormattedMessage.svelte';
export { default as AgentActivitySidebar } from './AgentActivitySidebar.svelte';
export { default as StatusIndicator } from './StatusIndicator.svelte';
export { default as Image } from './Image.svelte';

// Chat components
export {
	ChatEmptyState,
	ChatInput,
	ChatHistory,
	ChatMessage,
	SessionListItem,
	ChatDrawer,
	AgentTraceDrawer,
	AgentTracePanel
} from './chat';
export { ThinkingIndicator, MessageActions, SourcesList } from './chat/message';

// Source components
export { SourcesPanel, SourceItem, SourceDrawer } from './sources';
export * from './sources/types';

// Cluster components
export {
	ClusterTopology,
	MetricsGrid,
	QuickActions,
	ClusterHealthCard,
	BrokersGrid,
	TopicsPanel,
	ConsumerGroupsPanel,
	ClusterSwitcher
} from './cluster';

// Cluster page components
export {
	ConnectionStatus,
	ClusterStats,
	TopicsChips,
	OperationsPanel,
	QuickConnect,
	ConnectForm,
	SavedClusters
} from './cluster-page';

// Architecture components
export {
	PathSelector,
	SelectedPathInfo,
	QueryFlowGraph,
	AgentNode,
	ParallelNodes,
	FlowArrow,
	AllAgentsOverview,
	TechnologyStack,
	GraphStats,
	CallToAction
} from './architecture';
export * from './architecture/types';

// Documents components
export {
	IngestionForm,
	DocumentsTable,
	CollectionsOverview,
	SyncStatusPanel,
	SearchTab,
	BrowseTab,
	PipelineTab
} from './documents';
export * from './documents/types';

// Settings components
export { SettingsCard, FormField } from './settings';
export * from './settings/sections';
