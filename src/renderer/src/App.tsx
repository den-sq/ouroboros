import React, { useState } from 'react'
import MenuPanel from './components/MenuPanel/MenuPanel'
import SlicesPage from './routes/SlicesPage/SlicesPage'

import { DndContext, DragEndEvent, UniqueIdentifier, Active } from '@dnd-kit/core'

export const DragContext = React.createContext(null as any)

function App(): JSX.Element {
	const [active, setActive] = useState<Active | null>(null)
	const [parentChildData, setParentChildData] = useState<[UniqueIdentifier, Active] | null>(null)

	return (
		<>
			<DragContext.Provider value={{ active, parentChildData, setParentChildData }}>
				<DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
					<MenuPanel />
					<SlicesPage />
				</DndContext>
			</DragContext.Provider>
		</>
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

export default App
