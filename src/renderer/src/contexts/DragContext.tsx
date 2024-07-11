import { createContext, useState } from 'react'

import { DndContext, DragEndEvent, UniqueIdentifier, Active } from '@dnd-kit/core'

export type DragContextValue = {
	active: Active | null
	parentChildData: [UniqueIdentifier, Active] | null
	clearDragEvent: () => void
}

export const DragContext = createContext<DragContextValue>(null as any)

function DragProvider({ children }): JSX.Element {
	const [active, setActive] = useState<Active | null>(null)
	const [parentChildData, setParentChildData] = useState<[UniqueIdentifier, Active] | null>(null)

	const clearDragEvent = () => setParentChildData(null)

	return (
		<DragContext.Provider value={{ active, parentChildData, clearDragEvent }}>
			<DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
				{children}
			</DndContext>
		</DragContext.Provider>
	)

	function handleDragStart(event: DragEndEvent) {
		if (event.active) {
			setActive(event.active)
		}
	}

	function handleDragEnd(event: DragEndEvent) {
		if (event.over && event.active) {
			setParentChildData([event.over.id, event.active])
		}
		setActive(null)
	}
}

export default DragProvider
