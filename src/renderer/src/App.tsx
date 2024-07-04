import React, { useState } from 'react'
import MenuPanel from './components/MenuPanel/MenuPanel'
import SlicesPage from './routes/SlicesPage/SlicesPage'

import { DndContext, DragEndEvent, UniqueIdentifier, Active } from '@dnd-kit/core'

export const DragContext = React.createContext(null as any)

function App(): JSX.Element {
	const [parentChildData, setParentChildData] = useState<[UniqueIdentifier, Active] | null>(null)

	return (
		<>
			<DragContext.Provider value={{ parentChildData, setParentChildData }}>
				<DndContext onDragEnd={handleDragEnd}>
					<MenuPanel />
					<SlicesPage />
				</DndContext>
			</DragContext.Provider>
		</>
	)

	function handleDragEnd(event: DragEndEvent) {
		if (event.over && event.active) {
			setParentChildData([event.over.id, event.active])
		}
	}
}

export default App
