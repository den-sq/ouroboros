import { useDraggable } from '@dnd-kit/core'
import FileEntry from '../FileEntry/FileEntry'

function DraggableEntry({ name, path, type }) {
	const { attributes, listeners, setNodeRef } = useDraggable({
		id: path,
		data: {
			name,
			path,
			type,
			source: 'file-explorer'
		}
	})

	return (
		<div ref={setNodeRef} {...listeners} {...attributes}>
			<FileEntry name={name} path={path} type={type} />
		</div>
	)
}

export default DraggableEntry
