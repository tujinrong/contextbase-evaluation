package jhkcommon;

/**
 * TimerHandler.java
 * 
 * @date	H22.8.19	青木・浅見		センター集約対応なし
 * 
 */

/**
 * TimerHandler インターフェイス
 * 
 * タイマー機能で呼び出されるハンドラ
 */
public interface TimerHandler {
	/**
	 * 設定された時間になったときに呼び出されるメソッドです。
	 */
	public void handleTimer(Object userInfo);
}

