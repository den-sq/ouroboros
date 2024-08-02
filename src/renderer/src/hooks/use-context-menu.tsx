import { useState, useEffect, MouseEvent } from 'react'

// Based on code from:
// https://blog.logrocket.com/creating-react-context-menu/
function useContextMenu<T>(): {
	handleContextMenu: (event: MouseEvent, data?: T) => void
	clicked: boolean
	point: { x: number; y: number }
	data: T | null
} {
	const [clicked, setClicked] = useState(false)
	const [point, setPoint] = useState({
		x: 0,
		y: 0
	})
	const [data, setData] = useState<T | null>(null)

	useEffect(() => {
		const handleClick = (): void => {
			setClicked(false)
			setData(null)
		}

		document.addEventListener('click', handleClick)

		return (): void => {
			document.removeEventListener('click', handleClick)
		}
	}, [])

	function handleContextMenu(event: MouseEvent, data: T | null = null): void {
		event.preventDefault()
		event.stopPropagation()

		setClicked(true)
		setPoint({ x: event.pageX, y: event.pageY })
		setData(data)
	}

	return {
		handleContextMenu,
		clicked,
		point,
		data
	}
}

export default useContextMenu
