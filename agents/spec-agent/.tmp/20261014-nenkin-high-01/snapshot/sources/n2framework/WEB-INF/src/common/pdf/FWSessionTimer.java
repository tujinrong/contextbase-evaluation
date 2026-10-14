/*
 * 作成日: 2007/05/24
 *
 */
package common.pdf;

/*
 * FWSessionTimer.java
 */

/**
 * FWSessionTimer
 * 
 * タイマー機能
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public class FWSessionTimer implements java.lang.Runnable {
	private long _time;
	private FWTimerHandler _handler;
	private Thread _thread;
	private Object _userInfo = null;

	/**
	 * コンストラクタ.
	 */
	protected FWSessionTimer(long time, FWTimerHandler handler) {
		this.setTime(time);
		this.setHandler(handler);
	}

	/**
	 * コンストラクタ.
	 */
	protected FWSessionTimer(FWTimerHandler handler) {
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
			FWTimerHandler handler = this.getHandler();
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

	protected FWTimerHandler getHandler() {
		return _handler;
	}

	protected void setHandler(FWTimerHandler handler) {
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

