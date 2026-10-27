package jhkcommon;

/**
 * 
 * SessionTimer.java
 * 
 * 	@date	H22.8.19	青木・浅見		センター集約対応なし
 * 
 */

/**
 * SessionTimer
 * 
 * タイマー機能
 */
public class SessionTimer implements java.lang.Runnable {
	private long _time;
	private TimerHandler _handler;
	private Thread _thread;
	private Object _userInfo = null;

	/**
	 * コンストラクタ.
	 */
	protected SessionTimer(long time, TimerHandler handler) {
		this.setTime(time);
		this.setHandler(handler);
	}

	/**
	 * コンストラクタ.
	 */
	protected SessionTimer(TimerHandler handler) {
		this.setHandler(handler);
	}

	/**
	 * タイマーを開始します。.
	 */
	protected void start() throws IllegalThreadStateException, SecurityException {
		this.setThread(new Thread(this));
		this.getThread().setDaemon(true);
		this.getThread().start();
	}

	/**
	 * タイマーを再開します。.
	 */
	protected void restart() throws IllegalThreadStateException, SecurityException {
		this.cancel();
		this.start();
	}

	/**
	 * タイマーをキャンセルします。.
	 */
	protected void cancel() {
		if (this.getThread() != null) {
			this.setThread(null);
		}
	}

	public void run() {
		long toWait = this.getTime();
		if (toWait > 0) {
			try {
				Thread.sleep(toWait);
			} catch (InterruptedException e) {
			}
		}
		Thread thread = this.getThread();
		if (thread == Thread.currentThread()) {
			TimerHandler handler = this.getHandler();
			synchronized (handler) {
				if (thread == Thread.currentThread()) {
					handler.handleTimer((Object)_userInfo);
				} else {
				}
			}
			this.setThread(null);
		} else {
		}
	}

	//--------------------------------------------------------------
	// getter / setter
	//--------------------------------------------------------------

	protected long getTime() {
		return _time;
	}

	protected void setTime(long time) {
		_time = time;
	}

	protected TimerHandler getHandler() {
		return _handler;
	}

	protected void setHandler(TimerHandler handler) {
		_handler = handler;
	}

	protected Thread getThread() {
		return _thread;
	}

	protected void setThread(Thread thread) {
		_thread = thread;
	}

	protected Object getUserInfo() {
		return _userInfo;
	}

	protected void setUserInfo(Object obj) {
		_userInfo = obj;
	}
}

